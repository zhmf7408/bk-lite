import dayjs from 'dayjs';

export interface ChartDataItem {
  name: string;
  value: number;
}

export interface SeriesDataItem {
  name: string;
  data: number[];
}

export interface LineBarChartData {
  categories: string[];
  values?: number[];
  series?: SeriesDataItem[];
}

export type PieChartData = ChartDataItem[];

/**
 * 通用数据转换函数
 * 支持多种数据格式转换为图表数据
 */
export class ChartDataTransformer {

  /**
   * 标准化 namespace.data 字段
   * 兼容两种格式：
   *   旧格式（提取后）: namespace.data 直接是数组 [[key, value], ...]
   *   新格式（直传）:   namespace.data 是 NATS 原始对象 { result, data: [...], message }
   */
  static normalizeNamespaceData(data: any): any[] {
    if (Array.isArray(data)) {
      return data;
    }
    if (data && typeof data === 'object' && Array.isArray(data.data)) {
      return data.data;
    }
    return [];
  }

  /**
   * 将归一化后的 nsData 数组转换为 { [category]: value } 映射
   * 支持 [{name, value}] 和 [[key, value]] 两种格式
   */
  private static nsDataToMap(nsData: any[]): { [key: string]: number } {
    const map: { [key: string]: number } = {};
    if (nsData.length === 0) return map;
    if (typeof nsData[0] === 'object' && !Array.isArray(nsData[0]) && 'name' in nsData[0] && 'value' in nsData[0]) {
      nsData.forEach((item: any) => {
        map[this.formatTimeValue(item.name)] = parseFloat(item.value) || 0;
      });
    } else {
      nsData.forEach((item: any[]) => {
        map[item[0]] = item[1];
      });
    }
    return map;
  }

  /**
   * 格式化时间显示
   */
  static formatTimeValue(value: any): string {
    if (typeof value === 'number') {
      // 数字时间戳
      return dayjs(value * 1000).format('MM-DD HH:mm:ss');
    } else if (typeof value === 'string') {
      // 检查是否是 ISO 8601 格式的时间字符串
      const dateValue = dayjs(value);
      if (dateValue.isValid()) {
        return dateValue.format('MM-DD HH:mm:ss');
      }
      // 如果不是有效的时间字符串，直接返回
      return value;
    }
    return String(value);
  }

  /**
   * 转换为折线图/柱状图数据格式
   */
  static transformToLineBarData(rawData: any): LineBarChartData {
    if (!rawData) {
      return { categories: [], values: [] };
    }

    if (Array.isArray(rawData) && rawData.length === 0) {
      return { categories: [], values: [] };
    }

    if (Array.isArray(rawData) && rawData.length > 0) {
      // 检查是否是新的对象格式 [{name: "xxx", count: 20}, ...]
      if (
        rawData[0] &&
        typeof rawData[0] === 'object' &&
        'name' in rawData[0] &&
        'count' in rawData[0]
      ) {
        const categories = rawData.map((item: any) => item.name);
        const values = rawData.map((item: any) => item.count);
        return { categories, values };
      }
      // 检查是否是多维数据（多个系列）
      else if (
        rawData[0] &&
        typeof rawData[0] === 'object' &&
        rawData[0].namespace_id &&
        rawData[0].data
      ) {
        const allCategoriesSet = new Set<string>();
        rawData.forEach((namespace: any) => {
          const nsData = this.normalizeNamespaceData(namespace.data);
          Object.keys(this.nsDataToMap(nsData)).forEach((k) => allCategoriesSet.add(k));
        });
        const categories = Array.from(allCategoriesSet).sort();

        const series = rawData.map((namespace: any) => {
          const dataMap = this.nsDataToMap(this.normalizeNamespaceData(namespace.data));
          return {
            name: namespace.namespace_id,
            data: categories.map((category) => dataMap[category] || 0),
          };
        });

        return { categories, series };
      } else {
        // 原有的二维数组格式 [[key, value], ...]
        const categories = rawData.map((item: any[]) => item[0]);
        const values = rawData.map((item: any[]) => item[1]);
        return { categories, values };
      }
    }

    // 处理单个namespace的情况
    if (rawData && rawData.namespace_id && rawData.data) {
      const dataMap = this.nsDataToMap(this.normalizeNamespaceData(rawData.data));
      const categories = Object.keys(dataMap).sort();
      return { categories, values: categories.map((k) => dataMap[k]) };
    }

    return { categories: [], values: [] };
  }

  /**
   * 转换为饼图数据格式
   */
  static transformToPieData(rawData: any): PieChartData {
    if (!rawData) {
      return [];
    }

    // namespace 数组格式：取第一个 namespace 的数据
    if (Array.isArray(rawData) && rawData.length > 0 && rawData[0]?.namespace_id) {
      return this.transformToPieData(this.normalizeNamespaceData(rawData[0].data).slice(0, 10));
    }

    // 单 namespace 对象格式
    if (!Array.isArray(rawData) && rawData.namespace_id) {
      return this.transformToPieData(this.normalizeNamespaceData(rawData.data).slice(0, 10));
    }

    // 直接是数组
    if (Array.isArray(rawData)) {
      if (rawData.length === 0) return [];

      // 对象格式 [{name, value}]
      if (typeof rawData[0] === 'object' && !Array.isArray(rawData[0]) && 'name' in rawData[0] && 'value' in rawData[0]) {
        return rawData.map((item: any) => ({
          name: this.formatTimeValue(item.name),
          value: parseFloat(item.value) || 0,
        }));
      }
      // 二维数组格式 [[timestamp, value], ...]
      if (Array.isArray(rawData[0]) && rawData[0].length >= 2) {
        return rawData.map((item: any[]) => ({
          name: this.formatTimeValue(item[0]),
          value: parseFloat(item[1]) || 0,
        }));
      }
    }

    return [];
  }

  /**
   * 检查数据是否为多系列格式 
   */
  static isMultiSeriesData(rawData: any): boolean {
    return Array.isArray(rawData) &&
      rawData.length > 0 &&
      rawData[0] &&
      typeof rawData[0] === 'object' &&
      rawData[0].namespace_id &&
      rawData[0].data;
  }

  /**
   * 检查数据是否有效
   */
  static hasValidData(data: LineBarChartData | PieChartData): boolean {
    if (Array.isArray(data)) {
      return data.length > 0;
    }
    return data.categories && data.categories.length > 0;
  }

  /**
   * 校验原始数据是否可以转换为折线图/柱状图数据
   */
  static validateLineBarData(rawData: any, errorMessage?: string): { isValid: boolean; message?: string } {
    // 数据为空时图表组件会显示 Empty 状态，不需要校验
    if (!rawData || (Array.isArray(rawData) && rawData.length === 0)) {
      return { isValid: true };
    }

    try {
      const transformedData = this.transformToLineBarData(rawData);

      if (!transformedData.categories || transformedData.categories.length === 0) {
        return { isValid: false, message: errorMessage || '数据格式不匹配' };
      }

      // 检查数值数据
      const hasValidData = transformedData.series
        ? transformedData.series.some(series =>
          series.data && series.data.length > 0 &&
          series.data.some(val => typeof val === 'number' && !isNaN(val))
        )
        : transformedData.values &&
        transformedData.values.some(val => typeof val === 'number' && !isNaN(val));

      if (!hasValidData) {
        return { isValid: false, message: errorMessage || '数据格式不匹配' };
      }

      return { isValid: true };
    } catch {
      return { isValid: false, message: errorMessage || '数据格式不匹配' };
    }
  }

  /**
   * 校验原始数据是否可以转换为饼图数据
   */
  static validatePieData(rawData: any, errorMessage?: string): { isValid: boolean; message?: string } {
    // 数据为空时图表组件会显示 Empty 状态，不需要校验
    if (!rawData) {
      return { isValid: true };
    }

    try {
      const transformedData = this.transformToPieData(rawData);

      if (!transformedData || transformedData.length === 0) {
        return { isValid: true }; // 空数据让图表组件自行处理
      }

      const hasValidValues = transformedData.some(item =>
        item && typeof item.value === 'number' && !isNaN(item.value) && item.value > 0
      );

      if (!hasValidValues) {
        return { isValid: false, message: errorMessage || '数据格式不匹配' };
      }

      return { isValid: true };
    } catch {
      return { isValid: false, message: errorMessage || '数据格式不匹配' };
    }
  }
}
