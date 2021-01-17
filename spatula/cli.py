import attr
import click
import importlib
import pprint
from typing import List
from scrapelib import Scraper
from .pages import ListPage
from .core import URL


def get_class(dotted_name: str):
    mod_name, cls_name = dotted_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


def _display(obj) -> str:
    if isinstance(obj, dict):
        return pprint.pformat(obj)
    elif hasattr(obj, "to_dict"):
        return pprint.pformat(obj.to_dict())
    else:
        return repr(obj)


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("class_name")
@click.option("-i", "--interactive")
@click.option("-d", "--data", multiple=True)
@click.option("-s", "--source")
def test(class_name: str, interactive: bool, data: List[str], source: str) -> None:
    Cls = get_class(class_name)
    s = Scraper()

    # special case for passing a single URL source
    if source:
        source = URL(source)

    # build fake input from command line data if present
    fake_input = {}
    for item in data:
        k, v = item.split("=", 1)
        fake_input[k] = v

    input_type = getattr(Cls, "input_type", None)
    if input_type:
        print(f"{Cls.__name__} expects input ({input_type.__name__}): ")
        for field in attr.fields(input_type):
            if field.name in fake_input:
                print(f"  {field.name}: {fake_input[field.name]}")
            elif interactive:
                fake_input[field.name] = click.prompt("  " + field.name)
            else:
                dummy_val = f"~{field.name}"
                fake_input[field.name] = dummy_val
                print(f"  {field.name}: {dummy_val}")

        page = Cls(input_type(**fake_input), source=source)
    else:
        page = Cls(fake_input, source=source)

    # fetch data after input is handled, since we might need to build the source
    page._fetch_data(s)

    if issubclass(Cls, ListPage):
        for i, item in enumerate(page.process_page()):
            print(f"{i}:", _display(item))
    else:
        print(_display(page.process_page()))


@cli.command()
@click.argument("workflow_name")
@click.option("-o", "--output-dir", default=None)
def scrape(workflow_name: str, output_dir: str) -> None:
    workflow = get_class(workflow_name)
    workflow.execute(output_dir=output_dir)


if __name__ == "__main__":
    cli()
