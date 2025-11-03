from datetime import datetime, timezone, timedelta
import logging
import re


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # noqa: F821
logger = logging.getLogger()

class Time_converter:
    def parse_hhmm_time(self, hhmm: str, current_utc: datetime) -> datetime:
        """Parse HHMM time string and return datetime, handling day rollover"""
        hour = int(hhmm[:2])
        minute = int(hhmm[2:])
        
        parsed_time = current_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If parsed time is in future, it's from yesterday
        if parsed_time > current_utc:
            parsed_time = parsed_time - timedelta(days=1)
        
        return parsed_time
    def parse_metar_time(self, day: int, hhmm: str, current_utc: datetime) -> datetime:
        """Parse METAR day+time and return datetime"""
        hour = int(hhmm[:2])
        minute = int(hhmm[2:])
        
        try:
            parsed_time = current_utc.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            # Day doesn't exist in current month, try previous month
            prev_month = current_utc.replace(day=1) - timedelta(days=1)
            parsed_time = prev_month.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            return parsed_time
        
        # If time is more than 24 hours in future, it's from last month
        if parsed_time > current_utc + timedelta(hours=24):
            prev_month = current_utc.replace(day=1) - timedelta(days=1)
            parsed_time = prev_month.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        
        return parsed_time


class Weather_test(Time_converter):
    # TODO test weather: Datis test is not implemented yet
    def datis_dep_arr_time_test(self, weather_data):
        current_utc = datetime.now(timezone.utc)
        two_hours_ago = current_utc - timedelta(hours=2)
        issues = []
        datis = weather_data.get('datis', {})
        if not datis:
            logger.error("No DATIS data found")
            return

        # Check ARR info time
        arr_info = datis.get('arr', '')
        arr_match = re.search(r'INFO [A-Z] (\d{4})Z', arr_info)
        if arr_info and arr_match:
            arr_time = self.parse_hhmm_time(arr_match.group(1), current_utc)
            if arr_time and arr_time < two_hours_ago:
                age_hours = (current_utc - arr_time).total_seconds() / 3600
                issues.append(f"ARR info is {age_hours:.1f} hours old (last updated: {arr_time.strftime('%H:%M')}Z)")
        else:
            issues.append("ARR info: Could not extract time")
        
        # Check DEP info time
        dep_info = datis.get('dep', '')
        dep_match = re.search(r'INFO [A-Z] (\d{4})Z', dep_info)
        if dep_match:
            dep_time = self.parse_hhmm_time(dep_match.group(1), current_utc)
            if dep_time and dep_time < two_hours_ago:
                age_hours = (current_utc - dep_time).total_seconds() / 3600
                issues.append(f"DEP info is {age_hours:.1f} hours old (last updated: {dep_time.strftime('%H:%M')}Z)")
        else:
            issues.append("DEP info: Could not extract time")

    def metar_time_test(self, weather_data, current_utc, two_hours_ago):
        issues = []
        # Check METAR time
        metar = weather_data.get('metar', '')
        metar_match = re.search(r'(METAR|SPECI) [A-Z]{4} (\d{2})(\d{4})Z', metar)
        if metar_match:
            day = int(metar_match.group(2))
            hhmm = metar_match.group(3)
            metar_time =  self.parse_metar_time(day, hhmm, current_utc)
            if metar_time and metar_time < two_hours_ago:
                issues.append(f"OLD METAR DETECTED: Time now {current_utc.strftime('%H:%M')}Z --  {metar}")
        else:
            issues.append(f"METAR: Could not extract time- {metar}")

        return issues
        