import os
from tree_sitter import Language, Node, Parser
import tree_sitter_javascript as tsjs
from neomodel import StructuredNode, StringProperty, config, IntegerProperty, RelationshipTo

from src.utils_neo4j import clear_db_file

# Configure the database connection
config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'

class CodeNode(StructuredNode):
    node_type = StringProperty()
    filename = StringProperty()
    byte_start = IntegerProperty()
    byte_end = IntegerProperty()
    content = StringProperty()
    child_order = IntegerProperty()
    parent = RelationshipTo('CodeNode', "is in")
    imported_in = RelationshipTo('CodeNode', "is imported in")
    

js_parser = Parser(Language(tsjs.language()))

def try_matching_import(node: Node, graph_node: CodeNode, file_path: str):
    if node.parent is not None and node.parent.parent is not None and node.parent.parent.parent is not None:
        statement = node.parent.parent.parent
        statement_string_children = [child for child in statement.children if child.type == 'string']
        if len(statement_string_children) > 0:
            statement_string_fragment = [ch.text for ch in statement_string_children[0].children if ch.type == 'string_fragment']
            if len(statement_string_fragment) > 0:
                import_file_relative = statement_string_fragment[0].decode()
                import_file_name = os.path.abspath("/".join(file_path.split("/")[:-1])+'/' + import_file_relative)
                imported_element = node.text.decode()
                method_declaration = CodeNode.nodes.get_or_none(content=imported_element, filename=import_file_name, node_type='export_specifier')
                if method_declaration is not None:
                    graph_node.imported_in.connect(method_declaration)
                    graph_node.save()

def refresh_code_files(files_deleted, files_modified, log_progess=False):
    print(f"Updating {len(files_deleted) + len(files_modified)} code files...")
    clear_db_file(files_deleted)
    tot = len(files_modified)
    for i_file, file in enumerate(files_modified):
        if log_progess:
            print(f"File {i_file + 1} / {tot}               ", end="\r")
        if file.endswith(".js"):
            parse_file(file)
    print("\nUpdating code done!")

def parse_file(file_path):
    # Read the files
    with open(file_path, 'rb') as f:
        content = f.read()
        tree = js_parser.parse(content)
    
    # Clear db
    clear_db_file([file_path])
    
    # Tree walk
    current_nodes = [{"parent": None, "node": tree.root_node, "order": 0}]
    while len(current_nodes) > 0:
        found_nodes = []
        for node_object in current_nodes:
            node: Node = node_object["node"]
            child_order = node_object["order"]
            graph_node = CodeNode(content=node.text.decode(), node_type=node.type,filename=file_path,
                                  byte_start=node.start_byte, byte_end=node.end_byte, child_order=child_order)
            parent: CodeNode = node_object["parent"]
            graph_node.save()
            if parent is not None:
                # Connect to parent
                graph_node.parent.connect(parent)
            if node.type == "import_specifier":
                # Connect to import
                try_matching_import(node, graph_node, file_path)
            if node.child_count > 0:
                found_nodes.extend([{"parent": graph_node, "node": x, "order": i} for i, x in enumerate(node.children)])
        current_nodes = found_nodes