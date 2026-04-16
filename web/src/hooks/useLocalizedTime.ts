import { useSession } from 'next-auth/react';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import { getStoredTimezone, normalizeTimezone } from '@/utils/userPreferences';

dayjs.extend(utc);
dayjs.extend(timezone);

export const useLocalizedTime = () => {
  const { data: session } = useSession();

  const currentTimezone = (session?.user as any)?.timezone
    || (session as any)?.timezone
    || (session as any)?.zoneinfo
    || getStoredTimezone();

  const convertToLocalizedTime = (
    isoString: string,
    format: string = 'YYYY-MM-DD HH:mm:ss'
  ): string => {
    if (!isoString) {
      return '';
    }

    if (!currentTimezone) {
      return dayjs(isoString).format(format);
    }

    try {
      const date = dayjs(isoString).tz(normalizeTimezone(currentTimezone));
      return date.format(format);
    } catch {
      return dayjs(isoString).format(format);
    }
  };

  return {
    convertToLocalizedTime,
  };
};
