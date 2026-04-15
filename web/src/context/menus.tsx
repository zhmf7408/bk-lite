import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { MenuItem } from '@/types/index';
import { useLocale } from '@/context/locale';
import { normalizeLocale } from '@/utils/userPreferences';

interface MenusContextType {
  configMenus: MenuItem[];
  loading: boolean;
}

const MenusContext = createContext<MenusContextType>({ configMenus: [], loading: false });

export const MenusProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [configMenus, setConfigMenus] = useState<MenuItem[]>([]);
  const { locale } = useLocale();

  useEffect(() => {
    const fetchMenus = async () => {
      const nextLocale = normalizeLocale(locale);
      setLoading(true);
      try {
        const response = await fetch(`/api/menu?locale=${nextLocale}`);
        if (!response.ok) {
          throw new Error('Failed to fetch menus');
        }
        const menus = await response.json();
        setConfigMenus(menus);
      } catch (error) {
        console.error('Failed to fetch menus:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMenus();
  }, [locale]);

  return (
    <MenusContext.Provider value={{configMenus, loading}}>
      {children}
    </MenusContext.Provider>
  );
};

export const useMenus = () => {
  return useContext(MenusContext);
};
