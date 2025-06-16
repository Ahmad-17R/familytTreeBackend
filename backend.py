import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import json
import numpy as np

# Use non-interactive backend for robust PNG saving
matplotlib.use('agg')

def create_family_tree_graph(data):
    print("🔥 POST /generate-family-tree HIT")
    # Initialize directed graph
    G = nx.DiGraph()
    
    # Parse JSON data
    family_data = json.loads(data)
    
    # Add all nodes
    for person in family_data:
        G.add_node(person)
    
    # Find root node
    root = None
    for person, info in family_data.items():
        if 'root' in info.lower():
            root = person
            break
    
    if not root:
        raise ValueError("No root node found in the data")

    # Add edges based on relationships and status
    for person, info in family_data.items():
        relation_info = info.split(':')
        related_str = relation_info[0]  # e.g., "Stedelberto de Carugo_child"
        status = relation_info[1] if len(relation_info) > 1 else ''  # e.g., "Confirmed" or "Null"
        
        # Extract related person and relation type (case-insensitive)
        related_person = None
        relation_type = None
        for rel_type in ['spouse', 'child', 'anchor', 'parent']:
            suffix = f"_{rel_type}"
            if suffix.lower() in related_str.lower():
                # Find the exact key in family_data
                for key in family_data:
                    if key.lower() == related_str.replace(suffix, '').lower():
                        related_person = key
                        relation_type = rel_type
                        break
                break
        else:
            continue  # No valid relation type
        
        # Debug: Print parsed relationship
        print(f"Parsed: {person} -> {related_person} ({relation_type}, {status})")
        
        # Add edges if status is Confirmed or Probable
        if related_person in family_data and status in ['Confirmed', 'Probable']:
            if relation_type == 'spouse':
                G.add_edge(related_person, person, relation='spouse', status=status)
                G.add_edge(person, related_person, relation='spouse', status=status)  # Bidirectional
            elif relation_type == 'child':
                G.add_edge(person, related_person, relation='child', status=status)  # Child -> Parent
            elif relation_type == 'anchor':
                G.add_edge(person, related_person, relation='anchor', status=status)  # Anchor -> Host
            elif relation_type == 'parent':
                G.add_edge(person, related_person, relation='child', status=status)  # Parent -> Child

    # Debug: Print edges
    print("Edges in graph:", G.edges(data=True))
    
    # Assign positions based on hierarchy
    pos = {}
    y_level = 0  # Root at y=0
    x_offset = 1.5  # Horizontal spacing for children
    spouse_offset = x_offset / 2  # Half spacing for spouses
    y_offset = 1.0  # Vertical spacing
    anchor_offset = 0.5  # Anchor offset

    # Build hierarchy (parent -> children)
    children_by_parent = {}
    for person in family_data:
        children_by_parent[person] = []  # Initialize all nodes as potential parents
    for person, info in family_data.items():
        relation_info = info.split(':')
        related_str = relation_info[0]
        for rel_type in ['child']:
            suffix = f"_{rel_type}"
            if suffix.lower() in related_str.lower():
                # Find the exact parent key
                for key in family_data:
                    if key.lower() == related_str.replace(suffix, '').lower():
                        children_by_parent[key].append(person)
                        break

    # Assign levels (root at 0, children at -1, grandchildren at -2, etc.)
    levels = {root: 0}
    def assign_levels(node, level):
        levels[node] = level
        children = children_by_parent.get(node, [])
        for child in children:
            assign_levels(child, level - 1)
    
    assign_levels(root, 0)

    # Assign positions recursively
    def assign_positions(node, x, y, is_root=False):
        if node in pos:
            return  # Skip if already positioned
        pos[node] = (x, y)
        print(f"Assigned position: {node} at {pos[node]}")  # Debug
        
        # Place children
        children = children_by_parent.get(node, [])
        n_children = len(children)
        child_positions = []
        if n_children > 0:
            total_width = (n_children - 1) * x_offset
            start_x = x - total_width / 2
            for i, child in enumerate(children):
                child_x = start_x + i * x_offset
                assign_positions(child, child_x, y - y_offset)
                child_positions.append(child_x)
        
        # Adjust node's x-coordinate to center above children (especially for root)
        if n_children > 0 and is_root:
            center_x = sum(child_positions) / n_children
            pos[node] = (center_x, y)
            print(f"Adjusted position: {node} at {pos[node]}")  # Debug
        
        # Place spouse
        spouse = None
        for person, info in family_data.items():
            if f"{node}_spouse".lower() in info.lower() or f"{node}_Spouse".lower() in info.lower():
                spouse = person
                pos[spouse] = (pos[node][0] + spouse_offset, y)
                print(f"Assigned position: {spouse} at {pos[spouse]}")  # Debug
        
        # Place anchor
        anchor = None
        for person, info in family_data.items():
            if f"{node}_anchor".lower() in info.lower():
                anchor = person
                pos[anchor] = (pos[node][0] + anchor_offset, y - anchor_offset)
                print(f"Assigned position: {anchor} at {pos[anchor]}")  # Debug
                assign_positions(anchor, pos[anchor][0], pos[anchor][1])

    # Start positioning from root, marking it as root for centering
    assign_positions(root, 0, 0, is_root=True)

    # Process any unpositioned nodes with relations
    for person, info in family_data.items():
        if person not in pos:
            related_str = info.split(':')[0]
            for rel_type in ['spouse', 'anchor', 'child']:
                suffix = f"_{rel_type}"
                if suffix.lower() in related_str.lower():
                    # Find the exact related person key
                    related_person = None
                    for key in family_data:
                        if key.lower() == related_str.replace(suffix, '').lower():
                            related_person = key
                            break
                    if related_person in pos:
                        # Assign position relative to related person
                        if rel_type == 'spouse':
                            pos[person] = (pos[related_person][0] + spouse_offset, pos[related_person][1])
                            print(f"Assigned fallback position: {person} at {pos[person]}")  # Debug
                            assign_positions(person, pos[person][0], pos[person][1])
                        elif rel_type == 'anchor':
                            pos[person] = (pos[related_person][0] + anchor_offset, pos[related_person][1] - anchor_offset)
                            print(f"Assigned fallback position: {person} at {pos[person]}")  # Debug
                            assign_positions(person, pos[person][0], pos[person][1])
                        elif rel_type == 'child':
                            # Handle multiple children
                            children = [p for p in children_by_parent.get(related_person, []) if p not in pos]
                            n_children = len(children)
                            if n_children > 0:
                                total_width = (n_children - 1) * x_offset
                                start_x = pos[related_person][0] - total_width / 2
                                for i, child in enumerate(children):
                                    pos[child] = (start_x + i * x_offset, pos[related_person][1] - y_offset)
                                    print(f"Assigned fallback position: {child} at {pos[child]}")  # Debug
                                    assign_positions(child, pos[child][0], pos[child][1])
                        break

    # Position parents after all other nodes
    for person, info in family_data.items():
        related_str = info.split(':')[0]
        if '_parent'.lower() in related_str.lower():
            related_person = None
            for key in family_data:
                if key.lower() == related_str.replace('_parent', '').lower():
                    related_person = key
                    break
            if related_person in pos and person not in pos:
                pos[person] = (pos[related_person][0], pos[related_person][1] + y_offset)
                print(f"Assigned position: {person} at {pos[person]}")  # Debug

    # Debug: Print all positions
    print("All positions:", pos)

    # Create custom labels with dates and city
    labels = {}
    for person in family_data:
        info = family_data[person]
        parts = info.split(':')
        dates = parts[2] if len(parts) > 2 else ''
        city = parts[3] if len(parts) > 3 else ''
        labels[person] = f"{person}\n{dates}\n{city}" if dates and city else person

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Draw rounded rectangle nodes
    node_width = 0.38 # Increased width for better fit
    node_height = 0.06  # Height in data units (fits 3-line label)
    for node in G.nodes():
        x, y = pos[node]
        # Add rounded rectangle patch
        ax.add_patch(
            matplotlib.patches.FancyBboxPatch(
                (x - node_width / 2, y - node_height / 2),
                node_width,
                node_height,
                boxstyle='round,pad=0.05,rounding_size=0.05',
                facecolor='none',
                edgecolor='black',
                linewidth=1,
                alpha=0.8
            )
        )
    
    # Draw edges by status
    confirmed_edges = [(u, v) for u, v, d in G.edges(data=True) if d['status'] == 'Confirmed']
    probable_edges = [(u, v) for u, v, d in G.edges(data=True) if d['status'] == 'Probable']
    
    # Debug: Print edges being drawn
    print("Debug: Drawing confirmed edges:", confirmed_edges)
    print("Debug: Drawing probable edges:", probable_edges)
    
    # Draw confirmed edges (solid black, no arrows)
    if confirmed_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=confirmed_edges,
            edge_color='black',
            style='solid',
            width=2.0,
            arrows=False
        )
    
    # Draw probable edges (dotted black, no arrows)
    if probable_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=probable_edges,
            edge_color='black',
            style='dotted',
            width=1.5,
            arrows=False
        )

    # Draw labels (smaller font for multi-line text)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_weight='bold')
    
    # Add title
    plt.title("Family Tree Graph")
    
    # Save as PNG
    plt.savefig("family_tree.png", format="png", dpi=300, bbox_inches='tight')
    plt.close()

data = '''{
  "Stadelberto de Carugo": "root:Confirmed:890, 927:Carugo, Milano, etc.",
  "Andrei de loco Calugo": "Stadelberto de Carugo_anchor:Probable:990:Carugo, Monza",
  "Arnaldo de loco Calugo": "Andrei de loco Calugo_child:Confirmed:990:Carugo, Monza",
  "Garibaldo de loco Calugo": "Andrei de loco Calugo_child:Confirmed:990:Carugo, Monza",
  "Giovanni Rossi": "Arnaldo de loco Calugo_anchor:Probable:1200:Lahore",
  "Ficia de loco Modicia": "Garibaldo de loco Calugo_spouse:Confirmed:990:Carugo, Monza",
  "Ambroxi de Carugo": "Garibaldo de loco Calugo_anchor:Confirmed:1176:Como",
  "Aleena Rossi": "Giovanni Rossi_spouse:Probable:1202:lahore",
  "Tadoni de loco Modicia": "Ficia de loco Modicia_parent:Confirmed:990:Carugo, Monza",
  "Tomasso War": "Aleena Rossi_parent:Confirmed:1203:lahore"
}'''

create_family_tree_graph(data)