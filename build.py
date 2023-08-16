from __future__ import annotations
from expression.collections import Seq
from expression.core import Nothing, Option, Some
import sys
from utils import Course, PartialCourse, PrerequisiteType
from dataclasses import dataclass
from collections import deque


@dataclass(frozen=True, eq=True)
class AnnotatedCourse:
    course: Course
    annotation: Option[str]

    @staticmethod
    def of_str(s: str) -> Option[AnnotatedCourse]:
        split = s.split(" ")
        annotation = Some(" ".join(split[1:]).strip()) if len(split) > 1 else Nothing
        partial = PartialCourse.of_str(split[0].strip())
        if partial is Nothing:
            return Nothing
        course = Course.of_partial(partial.value)
        if course is Nothing:
            return Nothing
        return Some(AnnotatedCourse(course.value, annotation))


def get_lines(file: str) -> Seq[str]:
    return Seq.of_iterable(open(file, "r").readlines())


def main():
    if len(sys.argv) != 4:
        raise Exception(
            "Expected an input file. Usage: python build.py <input file> <edges_out> <nodes_out>"
        )
    input_lines = get_lines(sys.argv[1])
    core_courses = list(
        (
            input_lines.map(AnnotatedCourse.of_str)
            .filter(lambda course: course is not Nothing)
            .map(lambda course: course.value)
        ).to_list()
    )

    available_partials = set(
        map(PartialCourse.of_course, map(lambda c: c.course, core_courses))
    )

    COREQ_RELATIONS = [
        PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF,
        PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ALT,
        PrerequisiteType.CREDIT_OR_CONCURRENT_ONE_OF_ONLY,
    ]

    edges = []
    for course in core_courses:
        for prereq in course.course.prereq:
            for pre in prereq.courses:
                if pre in available_partials:
                    edges.append(
                        (
                            pre.dept + str(pre.num),
                            (course.course.dept + str(course.course.num)),
                            prereq.relation in COREQ_RELATIONS,
                        )
                    )

    edges_output = open(sys.argv[2], "w")
    edges_output.write(
        "export const edges = ["
        + ",".join(map(lambda e: f'["{e[0]}","{e[1]}", {str(e[2]).lower()}]', edges))
        + "];"
    )
    edges_output.close()

    nodes = []
    for course in core_courses:
        dept_num = course.course.dept + str(course.course.num)
        nodes.append(
            '{id: "'
            + dept_num
            + '", label: "'
            + dept_num
            + " "
            + (f"({course.course.name})" if len(course.course.name) > 0 else "")
            + course.annotation.map(lambda x: " " + x).default_value("")
            + '", dept: "'
            + course.course.dept
            + '", num: "'
            + str(course.course.num)
            + '"}'
        )

    nodes_output = open(sys.argv[3], "w")
    nodes_output.write(
        f"""
        export const nodes = [
            {",".join(nodes)}
        ];
    """
    )
    nodes_output.close()


if __name__ == "__main__":
    main()
