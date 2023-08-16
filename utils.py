from __future__ import annotations
from enum import Enum, IntEnum
from functools import lru_cache
from typing import List, TypeVar
import dataclasses
import requests
from expression import (
    effect,
    Success,
    compose,
    Error,
    Result,
    Option,
    Nothing,
    Some,
)
from expression.collections import FrozenList
import xml.etree.ElementTree as ET
import re
from functools import partial


def build_course_url(dept: str, num: int, term="fall", year=2023):
    url = f"https://courses.illinois.edu/cisapp/explorer/catalog/{year}/{term}/{dept.upper()}/{num}.xml"
    return url


def get_url(*args, **kwargs) -> Option[requests.Response]:
    return Option.of_obj(requests.get(*args, **kwargs)).filter(lambda r: r.ok)


class PrerequisiteType(IntEnum):
    ALL_OF = 0  # TODO: unsupported
    ONE_OF = 1
    ONE_OF_ALT = 2
    FRESHMAN_STANDING = 3
    SOPHOMORE_STANDING = 4
    JUNIOR_STANDING = 5
    SENIOR_STANDING = 6
    CREDIT_OR_CONCURRENT_ONE_OF = 7
    MAJORS_ONLY = 8
    DEPARTMENT_ONLY = 9
    ADEQUATE_ALEKS = 10
    CREDIT_OR_CONCURRENT_ONE_OF_ALT = 11  # really, CS advising?
    CREDIT_OR_CONCURRENT_ONE_OF_ONLY = 12 # REALLY?

    @staticmethod
    def of_str(s: str) -> Option[PrerequisiteType]:
        if "credit or concurrent registration in one of" in s:
            return Some(PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF)
        elif "credit or concurrent enrollment in" in s:
            return Some(PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ALT)
        elif "credit or concurrent registration in" in s:
            return Some(PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ONLY)
        elif "one of" in s:
            return Some(PrerequisiteType.ONE_OF)
        elif "freshman standing required" in s:
            return Some(PrerequisiteType.FRESHMAN_STANDING)
        elif "sophomore standing required" in s:
            return Some(PrerequisiteType.SOPHOMORE_STANDING)
        elif "junior standing required" in s:
            return Some(PrerequisiteType.JUNIOR_STANDING)
        elif "senior standing required" in s:
            return Some(PrerequisiteType.SENIOR_STANDING)
        elif "for majors only" in s:
            return Some(PrerequisiteType.MAJORS_ONLY)
        elif (
            "restricted to computer engineering or electrical engineering majors or transfer students with ece department consent"
            in s
        ):
            return Some(PrerequisiteType.DEPARTMENT_ONLY)
        elif (
            "an adequate aleks placement score as described at http://mathillinoisedu/aleks/, demonstrating knowledge of topics of"
            in s
        ):
            return Some(PrerequisiteType.ADEQUATE_ALEKS)
        elif "and" in s:
            return Some(PrerequisiteType.ALL_OF)
        else:
            return Nothing

    def __str__(self) -> str:
        if self == PrerequisiteType.ONE_OF:
            return "one of"
        elif self == PrerequisiteType.ONE_OF_ALT:
            return ""
        elif self == PrerequisiteType.ALL_OF:
            return "all of"
        elif self == PrerequisiteType.FRESHMAN_STANDING:
            return "freshman standing required"
        elif self == PrerequisiteType.SOPHOMORE_STANDING:
            return "sophomore standing required"
        elif self == PrerequisiteType.JUNIOR_STANDING:
            return "junior standing required"
        elif self == PrerequisiteType.SENIOR_STANDING:
            return "senior standing required"
        elif self == PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF:
            return "credit or concurrent registration in one of"
        elif self == PrerequisiteType.MAJORS_ONLY:
            return "for majors only"
        elif self == PrerequisiteType.DEPARTMENT_ONLY:
            return "restricted to computer engineering or electrical engineering majors or transfer students with ece department consent"
        elif self == PrerequisiteType.ADEQUATE_ALEKS:
            return "an adequate aleks placement score as described at http://mathillinoisedu/aleks/, demonstrating knowledge of topics of"
        elif self == PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ALT:
            return "credit or concurrent enrollment in"
        elif self == PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ONLY:
            return "credit or concurrent registration in"
        return "<<>>"


class Term(Enum):
    FALL = "fall"
    SPRING = "spring"


remove = lambda pattern: partial(re.sub, pattern, "")


@dataclasses.dataclass(frozen=True, eq=True)
class Prerequisite:
    courses: FrozenList[PartialCourse]
    relation: PrerequisiteType

    @staticmethod
    def of_str(st: str) -> Option[Prerequisite]:
        formatted_prereq = (
            Some(st)
            .map(remove(r"(s|S)ame as \w+ \d+"))
            .map(remove(r"(S|s)ee"))
            .map(remove(r"\."))
            .map(remove(r"(p|P)rerequisites?:"))
            .map(remove(r"is required")) # fixes credit or concurrent in x is required (boo chem dept)
            # .map(remove(r"and\s+"))  # don't consume and inside of st*and*ing
            .map(lambda s: s.strip())
            .map(lambda s: s.lower())
        ).default_value("")

        prereq_type = PrerequisiteType.of_str(formatted_prereq).default_value(
            PrerequisiteType.ONE_OF_ALT
        )

        course_list = formatted_prereq.replace(str(prereq_type), "").strip()

        first = FrozenList(
            re.split(r"(\s*,\s*|\s*or\s*|\s*and\s*)", course_list)
        ).filter(lambda x: x.strip() not in ["or", "and", ","])
        courses = (
            first.map(PartialCourse.of_str)
            .filter(lambda c: c is not Nothing)
            .map(lambda c: c.value)
        )

        return Some(Prerequisite(courses, prereq_type))


@dataclasses.dataclass(eq=True)
class Course:
    dept: str
    num: int
    prereq: FrozenList[Prerequisite]
    name: str

    @staticmethod
    def of_partial(partial: PartialCourse):
        course_xml = (
            get_url(build_course_url(partial.dept, partial.num))
            .map(lambda res: res.content)
            .map(lambda content: ET.fromstring(content))
        )
        course_info = course_xml.bind(
            lambda root: Option.of_optional(root.find("courseSectionInformation"))
        ).map(lambda info: info.text.lower())
        if "see" in course_info.default_value("") and "see class schedule" not in course_info.default_value(""):
            cleaned_info = course_info.default_value("").replace(".", "")
            duplicate = Course.of_partial(
                PartialCourse.of_str(
                    cleaned_info[cleaned_info.index("see") + len("see") :]
                ).value
            )
            return duplicate

        prerequisites = (
            course_info.filter(lambda info: "prerequisite:" in info)
            .map(
                lambda info: info[info.index("prerequisite:") + len("prerequisite:") :]
            )
            .map(Course._extract_prerequisites)
        ).default_value([])

        name = (
            course_xml.bind(lambda root: Option.of_optional(root.find("label")))
            .map(lambda name: name.text)
            .default_value("")
        )
        return Some(Course(partial.dept, partial.num, prerequisites, name))

    @staticmethod
    def _extract_prerequisites(prerequisites_str: str) -> FrozenList[Prerequisite]:
        return (
            FrozenList(re.split(r"(\.|;)", prerequisites_str))
            .filter(lambda s: s.strip() not in [";", ".", ""])
            .filter(lambda s: "students with previous" not in s.lower())
            .filter(lambda s: "https://" not in s.lower())
            .filter(lambda s: "edu" not in s.lower())
            .filter(lambda s: "illinois" not in s.lower())
            .filter(lambda s: "aleks" not in s.lower())
            .filter(lambda s: "high" not in s.lower())
            .map(Prerequisite.of_str)
            .filter(lambda x: x is not Nothing)
            .map(lambda x: x.value)
        )


@dataclasses.dataclass(frozen=True, eq=True)
class PartialCourse:
    dept: str
    num: int

    @staticmethod
    def of_str(s: str) -> Option[PartialCourse]:
        course_spec = s.upper().replace(" ", "")
        department = "".join(filter(lambda x: not x.isdigit(), course_spec))
        course = "".join(filter(lambda x: x.isdigit(), course_spec))
        if len(course) == 0:
            return Nothing
        res = Some(PartialCourse(department, int(course)))
        return res

    @staticmethod
    def of_course(course: Course) -> PartialCourse:
        return PartialCourse(course.dept, course.num)