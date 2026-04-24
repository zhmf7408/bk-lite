import React from 'react';
import { Drawer } from 'antd';
import { useTranslation } from '@/utils/i18n';

interface ContentDrawerProps {
  visible: boolean;
  onClose: () => void;
  content?: string;
  title?: string;
  width?: number;
  children?: React.ReactNode;
}

const ContentDrawer: React.FC<ContentDrawerProps> = ({ visible, onClose, content, title, width, children }) => {
  const { t } = useTranslation();

  const formatContent = (text: string) => {
    return text.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < text.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  return (
    <Drawer
      title={title || t('common.viewDetails')}
      placement="right"
      onClose={onClose}
      open={visible}
      width={width || 600}
    >
      {children ? children : (
        <div className="whitespace-pre-wrap leading-6">
          {content ? formatContent(content) : null}
        </div>
      )}
    </Drawer>
  );
};

export default ContentDrawer;