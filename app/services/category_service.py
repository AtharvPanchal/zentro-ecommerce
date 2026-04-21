from app.models import Category


# --------------------------------------------------
# 🔁 RECURSION HELPERS
# --------------------------------------------------

def is_circular(parent_id, child_id):
    while parent_id:
        if parent_id == child_id:
            return True
        parent = Category.query.get(parent_id)
        parent_id = parent.parent_id if parent else None
    return False


def get_depth(parent_id):
    depth = 0
    while parent_id:
        parent = Category.query.get(parent_id)
        if not parent:
            break
        depth += 1
        parent_id = parent.parent_id
    return depth


def get_all_subcategories(cat_id):
    subcategories = []

    children = Category.query.filter_by(parent_id=cat_id).all()

    for child in children:
        subcategories.append(child.id)
        subcategories.extend(get_all_subcategories(child.id))

    return subcategories


# --------------------------------------------------
# 🌳 TREE BUILDER (VERY USEFUL FOR UI)
# --------------------------------------------------

def build_category_tree(categories):
    tree = []
    lookup = {}

    # Step 1: map
    for cat in categories:
        cat.children_list = []
        lookup[cat.id] = cat

    # Step 2: build hierarchy
    for cat in categories:
        if cat.parent_id and cat.parent_id in lookup:
            parent = lookup[cat.parent_id]
            if parent:
                parent.children_list.append(cat)
        else:
            tree.append(cat)

    return tree


# --------------------------------------------------
# 📋 FLATTEN TREE (FOR DROPDOWN UI)
# --------------------------------------------------

def flatten_tree(tree, level=0):
    result = []

    for node in tree:
        node.level = level
        result.append(node)

        if hasattr(node, "children_list") and node.children_list:
            result.extend(flatten_tree(node.children_list, level + 1))

    return result