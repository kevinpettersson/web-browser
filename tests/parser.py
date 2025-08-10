from src.css_parser import CSSParser

if __name__ == "__main__":
    css = """
        p {
            color: red;
            font-size: 16px;
        }

        article div {
            margin-top: 10px;
        }
    """

    parser = CSSParser(css)
    rules = parser.parse()

    for selector, body in rules:
        print(f"Selector:{selector.tag}, body:{body}")