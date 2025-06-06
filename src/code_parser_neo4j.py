import os
from tree_sitter import Language, Node, Parser
import tree_sitter_javascript as tsjs
from neomodel import StructuredNode, StringProperty, config, IntegerProperty, RelationshipTo

from utils_neo4j import clear_db_file

# Configure the database connection
config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'

class CodeNode(StructuredNode):
    node_type = StringProperty()
    filename = StringProperty()
    byte_start = IntegerProperty()
    byte_end = IntegerProperty()
    content = StringProperty()
    parent = RelationshipTo('CodeNode', "IS_IN")
    children = RelationshipTo('CodeNode', "IS_FROM")
    imported_in = RelationshipTo('CodeNode', "IS_IMPORTED_IN")
    exported_to = RelationshipTo('CodeNode', "IS_EXPORTED_TO")
    

js_parser = Parser(Language(tsjs.language()))

def parse_file(file_path):
    # Read the files
    with open(file_path, 'rb') as f:
        content = f.read()
        tree = js_parser.parse(content)
    
    # Clear db
    clear_db_file([file_path])
    
    # Tree walk
    current_nodes = [{"parent": None, "node": tree.root_node}]
    while len(current_nodes) > 0:
        found_nodes = []
        for node_object in current_nodes:
            node: Node = node_object["node"]
            graph_node = CodeNode(content=node.text.decode(), node_type=node.type,filename=file_path,
                                  byte_start=node.start_byte, byte_end=node.end_byte)
            parent: CodeNode = node_object["parent"]
            graph_node.save()
            if parent is not None:
                # Connect to parent
                graph_node.parent.connect(parent)
                parent.children.connect(graph_node)
                parent.save()
            if node.type == "import_specifier":
                # Connect to import
                # FIXME existance check
                statement = node.parent.parent.parent
                import_file_relative = [ch.text for ch in [child for child in statement.children if child.type == 'string'][0].children if ch.type == 'string_fragment'][0].decode()
                import_file_name = os.path.abspath("/".join(file_path.split("/")[:-1])+'/' + import_file_relative)
                imported_element = node.text.decode()
                method_declaration = CodeNode.nodes.get(content=imported_element, filename=import_file_name, node_type='export_specifier')
                method_declaration.exported_to.connect(graph_node)
                graph_node.imported_in.connect(method_declaration)
                method_declaration.save()
            graph_node.save()
            if node.child_count > 0:
                found_nodes.extend([{"parent": graph_node, "node": x} for x in node.children])
        current_nodes = found_nodes

parse_file('/home/florian/ws/copicrotte/data/code-repository/PrimeNumber.js')
parse_file('/home/florian/ws/copicrotte/data/code-repository/AllPrimeNumber.js')