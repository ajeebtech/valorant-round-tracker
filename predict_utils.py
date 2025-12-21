"""
Utility functions for parsing timer predictions that include both time and color.
"""

def parse_prediction(class_name):
    """
    Parse a class name like '1_14_white' or '0_45_red' into time and color.
    
    Args:
        class_name: String like '1_14_white', '0_45_red', etc.
    
    Returns:
        tuple: (time_str, color) or (None, None) if parsing fails
        Example: ('1:14', 'white') or ('0:45', 'red')
    """
    try:
        # Split on last underscore to separate time and color
        parts = class_name.rsplit('_', 1)
        if len(parts) == 2:
            time_part, color = parts
            # Convert time from '1_14' to '1:14'
            time_str = time_part.replace('_', ':')
            return (time_str, color.lower())
        return (None, None)
    except:
        return (None, None)


def format_prediction(class_name, confidence=None):
    """
    Format a prediction into a readable string.
    
    Args:
        class_name: String like '1_14_white'
        confidence: Optional confidence score (0-1)
    
    Returns:
        str: Formatted prediction string
    """
    time_str, color = parse_prediction(class_name)
    if time_str and color:
        result = f"Time: {time_str}, Color: {color}"
        if confidence is not None:
            result += f" (confidence: {confidence:.2%})"
        return result
    return f"Class: {class_name}"


# Example usage:
if __name__ == '__main__':
    # Test parsing
    test_classes = ['1_14_white', '0_45_red', '1_300_white', '0_12_red']
    
    print("Prediction parsing examples:")
    for cls in test_classes:
        time, color = parse_prediction(cls)
        print(f"  {cls} → time='{time}', color='{color}'")
        print(f"    Formatted: {format_prediction(cls, 0.95)}")

