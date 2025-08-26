from typing import TypedDict

class BoundingBox(TypedDict):
    left: float
    top: float
    width: float
    height: float

class CenterPoint(TypedDict):
    x: float
    y: float

class InteractiveElement(TypedDict):
    tag: str
    role: str
    name: str
    attributes: dict[str, str]
    box: BoundingBox
    center: CenterPoint
    xpath: str

class InformativeElement(TypedDict):
    tag: str
    role: str
    content: str
    center: CenterPoint
    xpath: str

class ScrollableElement(TypedDict):
    tag: str
    role: str
    name: str
    attributes: dict[str, str]
    xpath: str

class DOMState(TypedDict):
    interactive_elements: list[InteractiveElement]
    informative_elements: list[InformativeElement]
    scrollable_elements: list[ScrollableElement]