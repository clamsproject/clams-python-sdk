# check for dependencies
SHELL := /bin/bash
deps = curl jq git python3 
check_deps := $(foreach dep,$(deps), $(if $(shell which $(dep)),some string,$(error "No $(dep) in PATH!")))

# constants
packagename = clams
generatedcode = $(packagename)/ver
sdistname = $(packagename)-python
bdistname = $(packagename)_python
artifact = build/lib/$(packagename)
buildcaches = build/bdist* $(bdistname).egg-info __pycache__
testcaches = .hypothesis .pytest_cache .pytype coverage.xml htmlcov .coverage

.PHONY: all
.PHONY: clean
.PHONY: test
.PHONY: develop
.PHONY: publish
.PHONY: docs
.PHONY: package
.PHONY: devversion

all: version test build

develop: devversion package test
	python3 setup.py develop --uninstall
	python3 setup.py develop
	twine upload --repository-url http://morbius.cs-i.brandeis.edu:8081/repository/pypi-develop/ \
		-u clamsuploader -p $$CLAMSUPLOADERPASSWORD dist/$(sdistname)-`cat VERSION`.tar.gz

publish: distclean version package test 
	test `git branch --show-current` = "master"
	@git tag `cat VERSION` 
	@git push origin `cat VERSION`

$(generatedcode): VERSION
	python3 setup.py donothing

docs: VERSION $(generatedcode)
	rm -rf documentation/_build docs
	python3 clams/appmetadata/__init__.py > documentation/appmetadata.jsonschema
	python3 setup.py build_sphinx -a
	mv documentation/_build/html docs
	mv documentation/appmetadata.jsonschema docs/
	touch docs/.nojekyll
	echo 'sdk.clams.ai' > docs/CNAME

package: VERSION
	pip install --upgrade -r requirements.dev
	python3 setup.py sdist

build: $(artifact)
$(artifact):
	python3 setup.py build

# invoking `test` without a VERSION file will generated a dev version - this ensures `make test` runs unmanned
test: devversion $(generatedcode)
	pip install --upgrade -r requirements.dev
	pip install -r requirements.txt
	pytype $(packagename)
	python3 -m pytest --cov=$(packagename) --cov-report=xml

# helper functions
e :=
space := $(e) $(e)
## handling version numbers
macro = $(word 1,$(subst .,$(space),$(1)))
micro = $(word 2,$(subst .,$(space),$(1)))
patch = $(word 3,$(subst .,$(space),$(1)))
increase_patch = $(call macro,$(1)).$(call micro,$(1)).$$(($(call patch,$(1))+1))
## handling versioning for dev version
add_dev = $(call macro,$(1)).$(call micro,$(1)).$(call patch,$(1)).dev1
split_dev = $(word 2,$(subst .dev,$(space),$(1)))
increase_dev = $(call macro,$(1)).$(call micro,$(1)).$(call patch,$(1)).dev$$(($(call split_dev,$(1))+1))

devversion: VERSION.dev VERSION; cat VERSION
version: VERSION; cat VERSION

VERSION.dev: devver := $(shell curl -s -X GET 'http://morbius.cs-i.brandeis.edu:8081/service/rest/v1/search?name=$(sdistname)' | jq '. | .items[].version' -r | sort -V | tail -n 1)
VERSION.dev:
	if [[ $(devver) == *.dev* ]]; then echo $(call increase_dev,$(devver)) ; else echo $(call add_dev,$(call increase_patch, $(devver))); fi \
	> VERSION.dev

VERSION: version := $(shell git tag | sort -r | head -n 1)
VERSION:
	@if [ -e VERSION.dev ] ; \
	then cp VERSION.dev VERSION; \
	else (read -p "Current version is ${version}, please enter a new version (default: increase *patch* level by 1): " new_ver; \
		[ -z $$new_ver ] && echo $(call increase_patch,$(version)) || echo $$new_ver) > VERSION; \
	fi

distclean:
	@rm -rf dist $(artifact) build/bdist*
clean: distclean
	@rm -rf VERSION VERSION.dev $(testcaches) $(buildcaches) $(generatedcode)
