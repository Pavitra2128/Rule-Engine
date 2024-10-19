from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

class Node:
    def __init__(self, node_type, value=None):
        self.type = node_type  # "operator" or "operand"
        self.value = value      # This can be the operator or condition value
        self.left = None        # Left child for binary operators
        self.right = None       # Right child for binary operators

    def __repr__(self):
        return f"Node(type={self.type}, value={self.value})"

    def to_dict(self):
        """Convert the Node to a dictionary for JSON serialization."""
        return {
            'type': self.type,
            'value': self.value,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

def create_rule(rule_string):
    def parse_expression(expr):
        expr = expr.strip()

        # Handle parentheses
        if expr.startswith("(") and expr.endswith(")"):
            return parse_expression(expr[1:-1])  # Remove outer parentheses

        # Recursive parsing for AND and OR
        for op in ["AND", "OR"]:
            parts = expr.split(f" {op} ")
            if len(parts) > 1:
                operator_node = Node("operator", op)
                operator_node.left = parse_expression(parts[0].strip())
                operator_node.right = parse_expression(" ".join(parts[1:]).strip())
                return operator_node
        
        # Base case: Check for a condition (like "age > 30")
        return parse_operand(expr)

    def parse_operand(operand):
        # Split the operand into attribute, operator, and value
        parts = operand.split()
        
        if len(parts) < 3:
            raise ValueError("Incomplete operand: must include attribute, operator, and value.")
        
        attribute = parts[0]
        operator = parts[1]
        value = " ".join(parts[2:]).strip("'")  # Handle cases where value may contain spaces
        return Node("operand", f"{attribute} {operator} {value}")

    # Start parsing the entire rule string
    return parse_expression(rule_string)

def combine_rules(rules):
    if not rules:
        return None

    asts = [create_rule(rule) for rule in rules]

    # Count operators to decide on the combining strategy
    operator_counts = {'AND': 0, 'OR': 0}
    for rule in rules:
        for op in operator_counts.keys():
            operator_counts[op] += rule.count(op)

    # Choose the most frequent operator as the root operator
    root_operator = 'AND' if operator_counts['AND'] >= operator_counts['OR'] else 'OR'
    combined_node = Node("operator", root_operator)

    # Start combining ASTs
    current = combined_node
    for ast in asts:
        if current.left is None:
            current.left = ast
        else:
            # Create a new operator node to combine the existing left node with the new AST
            new_operator = Node("operator", root_operator)
            new_operator.left = current.left
            new_operator.right = ast
            current.left = new_operator

    return combined_node

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_rule', methods=['POST'])
def create_rule_endpoint():
    data = request.json
    rule_string = data.get('rule_string', '')

    try:
        ast = create_rule(rule_string)
        return jsonify({'ast': ast.to_dict()})  # Convert Node to dict for JSON serialization
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/combine_rules', methods=['POST'])
def combine_rules_endpoint():
    data = request.json
    rules = data.get('rules', [])

    try:
        combined_ast = combine_rules(rules)
        return jsonify({'combined_ast': combined_ast.to_dict()})  # Convert Node to dict for JSON serialization
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
