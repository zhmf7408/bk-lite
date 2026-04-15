import type { ReactNode } from 'react';

interface ModelOptionLike {
  name: string;
  vendor_name?: string | null;
}

export const getModelOptionText = (model: ModelOptionLike): string => {
  return model.vendor_name ? `${model.name} (${model.vendor_name})` : model.name;
};

export const renderModelOptionLabel = (model: ModelOptionLike): ReactNode => {
  return (
    <>
      <span>{model.name}</span>
      {model.vendor_name ? <span style={{ color: 'var(--color-text-3)' }}> ({model.vendor_name})</span> : null}
    </>
  );
};

export const filterModelOption = (input: string, option?: { title?: string | number | null }): boolean => {
  return String(option?.title || '').toLowerCase().includes(input.toLowerCase());
};
