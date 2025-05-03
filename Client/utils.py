import os
import datetime

PATH = os.path.dirname(os.path.realpath(__file__))
TITLE = 'Project by Ron Katz & Tomer Mazurov'
FONT = 'Roboto Slab Regular'

class Colors:
    gray_14    = '#242424'
    gray_20    = '#333333'
    gray_24    = '#3d3d3d'
    gray_28    = "#474747"
    gray_32    = '#525252'
    gray_40    = '#666666'
    gray_52    = '#858585'
    gray_72    = '#b8b8b8'
    gray_92    = '#ebebeb'
    white      = '#ffffff'
    blue       = '#1f5fae'
    blue_hover = '#4468c2'
    red        = '#cc3038'
    red_hover  = '#932329'
    text_green = '#19e620'
    text_red   = '#ff3636',

def bytes_to_higher(b: int):
    KB = 1024
    MB = 1024 * KB
    GB = 1024 * MB
    
    if b < KB:
        return f'{b} B'
    elif b < MB:
        return f'{round(b / KB, 1)} KB'
    elif b < GB:
        return f'{round(b / MB, 1)} MB'
    else:
        return f'{round(b / GB, 1)} GB'
    
def get_upload_date(timestamp: int) -> str:
    local_timezone = datetime.datetime.now().astimezone().tzinfo
    local_time = datetime.datetime.fromtimestamp(timestamp, local_timezone)
    return local_time.strftime('%d/%m/%Y')