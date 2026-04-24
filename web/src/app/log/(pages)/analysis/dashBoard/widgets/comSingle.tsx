import React, { useEffect, useState, useRef } from 'react';
import { Spin, Empty } from 'antd';

interface ComSingleProps {
  rawData: any;
  loading?: boolean;
  config?: any;
}

const ComSingle: React.FC<ComSingleProps> = ({
  rawData,
  loading = false,
  config
}) => {
  const [displayValue, setDisplayValue] = useState<number>();
  const [fontSize, setFontSize] = useState<number>(100);
  const containerRef = useRef<HTMLDivElement>(null);

  // 处理数据
  useEffect(() => {
    if (!loading && rawData) {
      let value = config?.getData?.(rawData);
      // fallback: 没有 getData 时，通过 displayMaps 从 rawData 中提取值
      if (value === undefined && config?.displayMaps?.value) {
        const field = config.displayMaps.value;
        if (Array.isArray(rawData) && rawData.length > 0) {
          const parsed = parseFloat(rawData[0][field]);
          value = isNaN(parsed) ? undefined : parsed;
        } else if (rawData && typeof rawData === 'object' && !Array.isArray(rawData)) {
          const parsed = parseFloat(rawData[field]);
          value = isNaN(parsed) ? undefined : parsed;
        }
      }
      setDisplayValue(value);
    }
  }, [rawData, loading]);

  // 动态调整字体大小
  useEffect(() => {
    const updateFontSize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = containerRef.current.clientHeight;
        const digits = String(displayValue ?? '').length || 1;

        // 高度约束：确保文本不超出容器高度（lineHeight=1.2）
        const maxByHeight = containerHeight / 1.2;
        // 宽度约束：每个数字约 0.65em 宽
        const maxByWidth = containerWidth / (digits * 0.65);
        const calculatedSize = Math.max(
          24,
          Math.min(maxByHeight, maxByWidth, 300)
        );
        setFontSize(calculatedSize);
      }
    };

    updateFontSize();

    // 监听容器大小变化
    const resizeObserver = new ResizeObserver(() => {
      updateFontSize();
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [displayValue]);

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Spin size="small" />
      </div>
    );
  }

  if (!displayValue && displayValue !== 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-full w-full flex items-center justify-center"
    >
      <div
        className="font-bold text-center select-none transition-all duration-300"
        style={{
          fontSize: `${fontSize}px`,
          color: config?.color || 'var(--color-primary)',
          lineHeight: 1.2
        }}
      >
        {displayValue}
      </div>
    </div>
  );
};

export default ComSingle;
