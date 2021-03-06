from importlib import import_module
import fnmatch
import re


class YExample:
    def __init__(self, name, raw):
        self.name = name
        self.raw = (
            raw[1:] if raw.startswith("\n") else raw
        )  # cosmetic cleanup, most examples will be multiline and start with a newline
        self.output = None
        self.alerts = []

    def run(self):
        from yesses import Runner
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory(prefix="yesses-test") as td:
            tempdir = Path(td)
            configfile = tempdir / Path("config.yml")
            configfile.write_text("run:\n" + self.raw)
            with open(configfile, "r") as f:
                runner = Runner(f, fresh=True)
                runner.run()
                self.output = runner.config.findingslist.current_findings
                self.alerts = runner.config.alertslist.alerts


class YModule:
    def __init__(self, step, **kwargs):
        self.step = step
        self.__input_validation(kwargs)
        self.__create_result_dict()

    def __input_validation(self, kwargs):
        for field, properties in self.INPUTS.items():
            self.__check_required_field(field, properties, kwargs)
            self.__check_required_keys(field, properties, kwargs)
            self.__unwrap_field(field, properties, kwargs)
            setattr(self, field, kwargs[field])

    def __check_required_field(self, field, properties, kwargs):
        if field in kwargs:
            return
        if "default" in properties:
            kwargs[field] = properties["default"]
        else:
            raise Exception(
                f"Missing input to module {self.__class__.__name__}: {field}"
            )

    def __check_required_keys(self, field, properties, kwargs):
        if properties["required_keys"] is None:
            return
        if field not in kwargs or kwargs[field] is None:
            return
        for el in kwargs[field]:
            if not isinstance(el, dict):
                raise Exception(
                    f"Field '{field}' should contain mappings with the keys {properties['required_keys']}. Element '{el}' is a {type(el)}."
                )
            for key in properties["required_keys"]:
                try:
                    el[key]
                except KeyError:
                    raise Exception(
                        f"In field '{field}': Missing key '{key}' on input element '{el}' in {self.step}."
                    )

    def __unwrap_field(self, field, properties, kwargs):
        if not properties.get("unwrap", False):
            return
        assert len(properties["required_keys"]) == 1
        kwargs[field] = list(
            el.get(properties["required_keys"][0]) for el in kwargs[field]
        )

    def __create_result_dict(self):
        self.results = {}
        for field, properties in self.OUTPUTS.items():
            if (
                "*" in field or "?" in field
            ):  # field names may contain placeholders; we skip these
                continue
            self.results[field] = []

    @classmethod
    def find_matching_output_field(cls, result_key):
        """First tries to match the non-wildcard keys, then the wildcard keys."""

        for output_field, properties in cls.OUTPUTS.items():
            if "*" in output_field or "?" in output_field:
                continue
            if result_key == output_field:
                return output_field, properties

        for output_field, properties in cls.OUTPUTS.items():
            if fnmatch.fnmatchcase(result_key, output_field):
                return output_field, properties

        raise Exception(
            f"Unknown output field found: {result_key}, does not match any of {', '.join(cls.OUTPUTS.keys())}"
        )

    def __check_output_types(self):
        output_fields_found = []
        for result_field, findings in self.results.items():
            output_field, properties = self.find_matching_output_field(result_field)
            output_fields_found.append(output_field)
            if properties["provided_keys"] is None:
                continue
            for el in findings:
                for key in properties["provided_keys"]:
                    try:
                        el[key]
                    except KeyError:
                        raise Exception(
                            f"In field {result_field}: Missing key '{key}' on output element '{el}' in {self.step}."
                        )

        if set(output_fields_found) != set(self.OUTPUTS.keys()):
            missing = set(self.OUTPUTS.keys()) - set(output_fields_found)
            breakpoint()
            raise Exception(
                f"Missing field(s) in output of {self.step}: {', '.join(missing)}"
            )

    @classmethod
    def selftest(cls, standalone=True):
        import logging
        import yaml

        if standalone:
            logging.getLogger().setLevel(logging.DEBUG)
        logging.info(f"Running examples in {cls.__name__}")
        if not hasattr(cls, "EXAMPLES"):
            return None
        for ex in cls.EXAMPLES:
            ex.run()
            res = yaml.safe_dump(ex.output, default_flow_style=False, default_style="")
            logging.debug(f"Findings:\n{res}")
        return True

    @staticmethod
    def class_from_string(action_string):
        verb, subj = action_string.split(" ", 1)
        cls = re.sub("( [a-z])", lambda match: match.group(1).upper(), subj)
        cls = cls.replace(" ", "")
        return getattr(import_module(f"yesses.{verb}"), cls)

    @classmethod
    def name(cls):
        name = re.sub(
            "([a-z]|[A-Z]+)([A-Z])",
            lambda match: f"{match.group(1)} {match.group(2)}",
            cls.__name__,
        )
        return name

    def run_module(self):
        self.run()
        self.__check_output_types()
        return self.results
