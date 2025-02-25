from collections import namedtuple
from uuid import UUID
import re
import html
import urllib


def _namedtuplefetchall(cursor):
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    results = []
    for row in cursor.fetchall():
        row_list = list(row)
        row_list[0] = UUID(row[0])
        results.append(nt_result(*row_list))
    return results

    # def get_queryset(self):
    #     with connection.cursor() as cursor:
    #         cursor.execute("SELECT * FROM {}".format(Event._meta.db_table))
    #         return _namedtuplefetchall(cursor) 

def sanitize_input(input_text: str) -> str:

    input_text = urllib.parse.unquote(input_text)

    input_text = html.unescape(input_text)

    if re.search(r'<[^0-9].*?>', input_text):
        escaped_text = html.escape(input_text, quote=False)
        sanitized_text = re.sub(r'&lt;.*?&gt;', '', escaped_text)
        return sanitized_text.strip()

    if '<' in input_text and re.search(r'<\d+', input_text):
        return input_text.strip()

    if '&' in input_text and not re.search(r'<.*?>', input_text):
        return input_text.strip()

    if re.search(r'[<>&]{2,}', input_text):
        return input_text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;').strip()
    
    return input_text.strip()