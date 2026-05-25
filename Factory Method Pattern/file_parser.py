# Author: Sparsha Srinath
# Topic: File Parser — Factory + Strategy
# Date: 2026-05-24
# Tags: design-patterns, factory, strategy, low-level-design
#
# Description:
#   A File Parser system that handles CSV, JSON, and XML files.
#   Uses Factory to pick the right parser based on file extension,
#   and Strategy since each parser implements parse() differently.
#
# Patterns:
#   - Factory: create_parser() picks the right parser from file extension
#   - Strategy: each parser implements parse() its own way
#
# This is both Factory AND Strategy:
#   - Factory aspect: deciding WHICH parser to create based on input
#   - Strategy aspect: each parser has a different algorithm for parsing
#
# Factory vs Strategy reminder:
#   - Factory: "I don't know which class to create — decide for me"
#   - Strategy: "I have multiple algorithms — let me swap them"
#   - Here both apply: factory decides which parser, strategy defines how it parses


import json
import csv
import io
from abc import ABC, abstractmethod


# ====================
# 1. Strategy — each parser implements parse() differently
# ====================

class FileParser(ABC):
    @abstractmethod
    def parse(self, content):
        pass


class JSONParser(FileParser):
    def parse(self, content):
        # json.loads converts JSON string to Python dict/list
        data = json.loads(content)
        print(f"JSON parsed: {len(data)} records")
        return data


class CSVParser(FileParser):
    def parse(self, content):
        # csv.DictReader converts CSV to list of dicts
        # each row becomes a dict with headers as keys
        reader = csv.DictReader(io.StringIO(content))
        data = list(reader)
        print(f"CSV parsed: {len(data)} records")
        return data


class XMLParser(FileParser):
    def parse(self, content):
        # simple XML parsing — find all tags and extract text
        # production code would use xml.etree.ElementTree
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        data = []
        for child in root:
            record = {}
            for field in child:
                record[field.tag] = field.text
            data.append(record)
        print(f"XML parsed: {len(data)} records")
        return data


# ====================
# 2. Factory — picks the right parser from file extension
#    Client doesn't know which parser class exists
#    Just passes a filename, gets the right parser back
# ====================

def create_parser(filename):
    # extract extension from filename
    extension = filename.rsplit(".", 1)[-1].lower()

    parsers = {
        "json": JSONParser,
        "csv": CSVParser,
        "xml": XMLParser,
    }

    if extension not in parsers:
        raise ValueError(f"Unsupported file type: .{extension}")

    return parsers[extension]()


# ====================
# 3. Facade — one simple function to parse any file
#    Combines factory + parsing in one call
# ====================

def parse_file(filename, content):
    parser = create_parser(filename)  # factory picks the right parser
    return parser.parse(content)      # strategy runs the right algorithm


# ====================
# Demo
# ====================

# JSON
json_content = '[{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]'
data = parse_file("users.json", json_content)
print(data)

# CSV
csv_content = "name,age\nAlice,30\nBob,25"
data = parse_file("users.csv", csv_content)
print(data)

# XML
xml_content = """<users>
    <user><name>Alice</name><age>30</age></user>
    <user><name>Bob</name><age>25</age></user>
</users>"""
data = parse_file("users.xml", xml_content)
print(data)

# Unknown type — raises error
try:
    parse_file("data.pdf", "some content")
except ValueError as e:
    print(e)  # Unsupported file type: .pdf
