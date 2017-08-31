#!/usr/bin/python3

import re

def split_indent_line(line):
    indent = []
    for char in line:
        if char.isspace():
            indent.append(char)
        else:
            return "".join(indent), line[len(indent):]
    return "", ""

def nest_indentation(text):
    result_stack = []
    current_level = []
    indent_stack = [0]
    for line_number, line in enumerate(text.splitlines()):
        indent, content = split_indent_line(line)
        if len(indent) > indent_stack[-1]:
            indent_stack.append(len(indent))
            result_stack.append(current_level)
            current_level = [content]
        elif len(indent) == indent_stack[-1]:
            current_level.append(content)
        else:
            while len(indent) < indent_stack[-1]:
                indent_stack.pop()
                new_current_level = result_stack.pop()
                new_current_level.append(current_level)
                current_level = new_current_level
            if len(indent) > indent_stack[-1]:
                raise Exception("Indentation error at line " + str(line_number))
            current_level.append(content)
    for indent in indent_stack[1:]:
        new_current_level = result_stack.pop()
        new_current_level.append(current_level)
        current_level = new_current_level
    return current_level

class Document:
    def __init__(self, children=[], parent=None):
        self.attributes = {}
        self.children = []
        self.content = []
        self.parent = parent
        self.flagged = False

    def flagNode(self):
        self.flagged = True

    def isFlagged(self):
        return self.flagged

    def appendDocument(self, document):
        self.children.append(document)
        document.parent = self

    def setAttribute(self, key, value):
        self.attributes[key] = value
        return self

    def getAttribute(self, key):
        return self.attributes.get(key, None)

    def addContent(self, line):
        self.content.append(line)

    def getChildren(self, level=0):
        # breadth first search
        yield (level, self)
        for child in self.children:
            for grandchild in child.getChildren(level + 1):
                yield grandchild

    def getChildrenAtLevel(self, level):
        if level == 0:
            yield self
        else:
            for child in self.children:
                for grandchild in child.getChildrenAtLevel(level - 1)
                    yield grandchild

class MoveOperation:
    def __init__(self, old_node, new_parent, level):
        self.node = old_node
        self.new_parent = new_parent
        self.level = level

class ModifyOperation:
    def __init__(self, old_node, attribute, new_value, level):
        self.node = old_node
        self.attribute = attribute
        self.new_value = new_value
        self.level = level

class DeleteOperation:
    def __init__(self, old_node, level):
        self.node = old_node
        self.level = level

class CreateOperation:
    def __init__(self, new_node, level):
        self.node = new_node
        self.level = level

attribute_regex = re.compile('[\w]+:.*')

def document_from_structure(structure):
    result = Document()
    for line in structure:
        if isinstance(line, list):
            result.appendDocument(document_from_structure(line))
        else:
            if attribute_regex.match(line):
                key, value = line.split(':', 1)
                value = value.strip()
                result = result.setAttribute(key, value)
            else:
                result.addContent(line)
    return result

def same_ids(x, y):
    return x.getAttribute('id') == y.getAttribute('id')

def document_diff(old, new, are_same=same_ids):
    result = []
    for level, old_child in old.getChildren():
        for new_child in new.getChildrenAtLevel(level):
            if are_same(old_child, new_child):
                # The node exists in the old and new graph
                # check if the node was moved or modified (or both)
                if old_child.parent != new_child.parent:
                    # The node has been moved
                    result.append(MoveOperation(old_child, new_child.parent, level))
                    new_child.setFlag()
                for attribute, new_value in old_child.getChangedAttributes(new_child):
                    # attribute, new value is an attribute that has changed
                    result.append(ModifyOperation(old_child, attribute, new_value, level))
                    new_child.setFlag()
                break
        else:
            # The node doesn't exist in the new graph
            # it was deleted
            result.append(DeleteOperation(old_child, level))
    for level, new_child in new.getChildren():
        # any nodes in the new graph that haven't been "flagged" are new
        if not new_child.isFlagged():
            result.append(CreateOperation(new_child, level))
    return result

