from enum import Enum
from typing import List


# Can be expanded for groups and other roles
class Role(Enum):
    PARTICIPANT = 0
    HOST = 1
    SERVER = 2


def get_role(staff, meeting) -> List[Role]:
    roles = []
    if meeting.host == staff.id:
        roles.append(Role.HOST)

    if staff.id in meeting.staff:
        roles.append(Role.PARTICIPANT)


    return roles
