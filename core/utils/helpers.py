from collections import namedtuple
from uuid import UUID

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