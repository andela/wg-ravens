'''return the range of days for the current month'''
from datetime import date, timedelta
import calendar


def get_month_range(start_date=None):
    '''calculate the month range'''
    if start_date is None:
        start_date = date.today().replace(day=1)
    month_range = calendar.monthrange(start_date.year, start_date.month)
    end_date = start_date + timedelta(days=month_range[1]-1)
    return (start_date, end_date)
'''return the range of days for the current month'''
from datetime import date, timedelta
import calendar


def get_month_range(start_date=None):
    '''calculate the month range'''
    if start_date is None:
        start_date = date.today().replace(day=1)
    month_range = calendar.monthrange(start_date.year, start_date.month)
    end_date = start_date + timedelta(days=month_range[1]-1)
    return (start_date, end_date)
