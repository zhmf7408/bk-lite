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

export class ChartDataTransformer {
  static isStructurallyEmpty(rawData: any): boolean {
    if (!rawData) return true;
    if (Array.isArray(rawData)) return rawData.length === 0;
    if (typeof rawData === 'object') return Object.keys(rawData).length === 0;
    return false;
  }

  private static dataToMap(data: any[]): { [key: string]: number } {
    const map: { [key: string]: number } = {};
    if (data.length === 0) return map;
    if (typeof data[0] === 'object' && !Array.isArray(data[0]) && 'name' in data[0] && 'value' in data[0]) {
      data.forEach((item: any) => {
        map[this.formatTimeValue(item.name)] = parseFloat(item.value) || 0;
      });
    } else if (Array.isArray(data[0]) && data[0].length >= 2) {
      data.forEach((item: any[]) => {
        map[this.formatTimeValue(item[0])] = item[1];
      });
    }
    return map;
  }

  static formatTimeValue(value: any): string {
    if (typeof value === 'number') {
      return dayjs(value * 1000).format('MM-DD HH:mm:ss');
    } else if (typeof value === 'string') {
      const dateValue = dayjs(value);
      if (dateValue.isValid()) {
        return dateValue.format('MM-DD HH:mm:ss');
      }
      return value;
    }
    return String(value);
  }

  static transformToLineBarData(rawData: any): LineBarChartData {
    if (!rawData) {
      return { categories: [], values: [] };
    }

    if (Array.isArray(rawData)) {
      if (rawData.length === 0) {
        return { categories: [], values: [] };
      }

      // [{name, count}] format
      if (rawData[0] && typeof rawData[0] === 'object' && 'name' in rawData[0] && 'count' in rawData[0]) {
        return {
          categories: rawData.map((item: any) => item.name),
          values: rawData.map((item: any) => item.count),
        };
      }

      // [{name, value}] format
      if (rawData[0] && typeof rawData[0] === 'object' && !Array.isArray(rawData[0]) && 'name' in rawData[0] && 'value' in rawData[0]) {
        return {
          categories: rawData.map((item: any) => this.formatTimeValue(item.name)),
          values: rawData.map((item: any) => parseFloat(item.value) || 0),
        };
      }

      // [[key, value], ...] format
      if (Array.isArray(rawData[0]) && rawData[0].length >= 2) {
        return {
          categories: rawData.map((item: any[]) => this.formatTimeValue(item[0])),
          values: rawData.map((item: any[]) => item[1]),
        };
      }

      return { categories: [], values: [] };
    }

    // Object-keyed multi-series: { seriesName: [[x,y], ...], ... }
    if (typeof rawData === 'object') {
      const keys = Object.keys(rawData);
      const isMultiSeries = keys.length > 0 && keys.every((k) => Array.isArray(rawData[k]));
      if (isMultiSeries) {
        const allCategoriesSet = new Set<string>();
        keys.forEach((k) => {
          rawData[k].forEach((item: any) => {
            if (Array.isArray(item) && item.length >= 2) {
              allCategoriesSet.add(this.formatTimeValue(item[0]));
            } else if (item && typeof item === 'object' && 'name' in item) {
              allCategoriesSet.add(this.formatTimeValue(item.name));
            }
          });
        });
        const categories = Array.from(allCategoriesSet).sort();
        const series = keys.map((k) => {
          const dataMap = this.dataToMap(rawData[k]);
          return {
            name: k,
            data: categories.map((cat) => dataMap[cat] || 0),
          };
        });
        return { categories, series };
      }
    }

    return { categories: [], values: [] };
  }

  static transformToPieData(rawData: any): PieChartData {
    if (!rawData) return [];

    if (Array.isArray(rawData)) {
      if (rawData.length === 0) return [];

      // [{name, value}]
      if (typeof rawData[0] === 'object' && !Array.isArray(rawData[0]) && 'name' in rawData[0] && 'value' in rawData[0]) {
        return rawData.map((item: any) => ({
          name: this.formatTimeValue(item.name),
          value: parseFloat(item.value) || 0,
        }));
      }

      // [[key, value], ...]
      if (Array.isArray(rawData[0]) && rawData[0].length >= 2) {
        return rawData.map((item: any[]) => ({
          name: this.formatTimeValue(item[0]),
          value: parseFloat(item[1]) || 0,
        }));
      }

      // [{name, count}]
      if (typeof rawData[0] === 'object' && 'name' in rawData[0] && 'count' in rawData[0]) {
        return rawData.map((item: any) => ({
          name: item.name,
          value: item.count,
        }));
      }
    }

    return [];
  }

  static isMultiSeriesData(rawData: any): boolean {
    if (!rawData || Array.isArray(rawData)) return false;
    if (typeof rawData === 'object') {
      const keys = Object.keys(rawData);
      return keys.length > 0 && keys.every((k) => Array.isArray(rawData[k]));
    }
    return false;
  }

  static hasValidData(data: LineBarChartData | PieChartData): boolean {
    if (Array.isArray(data)) {
      return data.length > 0;
    }
    return data.categories && data.categories.length > 0;
  }

  static validateLineBarData(rawData: any, errorMessage?: string): { isValid: boolean; message?: string } {
    if (this.isStructurallyEmpty(rawData)) {
      return { isValid: true };
    }

    try {
      const transformedData = this.transformToLineBarData(rawData);

      if (!transformedData.categories || transformedData.categories.length === 0) {
        return { isValid: false, message: errorMessage || '数据格式不匹配' };
      }

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

  static validatePieData(rawData: any, errorMessage?: string): { isValid: boolean; message?: string } {
    if (this.isStructurallyEmpty(rawData)) {
      return { isValid: true };
    }

    try {
      const transformedData = this.transformToPieData(rawData);

      if (!transformedData || transformedData.length === 0) {
        return { isValid: false, message: errorMessage || '数据格式不匹配' };
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
