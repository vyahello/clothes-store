#!/usr/bin/env bash

PACKAGE="./"


--entry-point-box() {
:<<DOC
    Provides pretty-printer check box
DOC
    printf "Start ${1} analysis ...\n"
}



check-black() {
:<<DOC
    Runs "black" code analyser
DOC
    --entry-point-box "black" && ( black --check ${PACKAGE} )
}


check-flake() {
:<<DOC
    Runs "flake8" code analyser
DOC
    --entry-point-box "flake" && ( flake8 ${PACKAGE} )
}


check-unittests() {
:<<DOC
    Runs unittests using "pytest" framework
DOC
    --entry-point-box "unitests" && pytest
}


main() {
:<<DOC
    Runs "main" code analyser
DOC
    check-black && check-flake
}


main