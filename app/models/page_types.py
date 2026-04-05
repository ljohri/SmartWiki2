from enum import StrEnum


class PageType(StrEnum):
    PROJECT = "project"
    CONCEPT = "concept"
    ENTITY = "entity"
    SOURCE_NOTE = "source-note"
    SYNTHESIS = "synthesis"
    DECISION = "decision"
    INDEX = "index"
    LOG = "log"


class PageStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
