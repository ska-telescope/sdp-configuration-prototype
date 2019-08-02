#!/bin/bash

# Runs one test at a time.
# Usage: run_c_tests.sh test
# Where test is one of:
#   - CPP (CPPCheck, CPP-check ...) for the CPP check
#   - USAN (undefinded, behaviour, ...) for the undefined behaviour check
#   - TSAN (thread, ...) for the thread sanity check
#   - ASAN (address ...) for the address sanity check
#   - COV (COVERALLS) Coveralls check
# The test argument can be upper or lower case.
# There are aliases for the sanity checks.

bold=$(tput bold)
normal=$(tput sgr0)

# Is this a better hack?
[[ -d /app ]] && cd /app

cd src/vis_receive
[[ -e ./build ]] && printf "\n**** deleting old build directory ****\n" && \
	rm -rf ./build

mkdir ./build
cd ./build
case ${1^^} in
    CPP*)
	echo -e "\n ${bold}*** Running Cpp Check *** ${normal} \n"
	cd ..
	cppcheck ./ -i extern/gtest/ --enable=warning,portability,style
	cd build
	;;
    USAN|UNDEF*|BEHAV*)
	echo -e "\n ${bold}*** Running Undefined Behaviour Sanitizer *** ${normal} \n"
	cmake -DENABLE_USAN=ON ..
	make
	./tests/recv_test
	;;
    TSAN|THREAD*)
	echo -e "\n ${bold}*** Running Threading Sanitizer *** ${normal} \n"
	cmake -DENABLE_TSAN=ON ..
	make
	./tests/recv_test
	;;
    ASAN|ADDRESS*)
	echo -e "\n ${bold}*** Running Address Sanitizer *** ${normal} \n"
	cmake -DENABLE_ASAN=ON ..
	make
	./tests/recv_test
	;;
    COV*)
	echo -e "\n ${bold}*** Running Coveralls *** ${normal} \n"
	cmake -DCOVERALLS=ON -DCMAKE_BUILD_TYPE=Debug ..
	make
	make coveralls
	;;
esac
cd ..
printf "\n**** No longer require build directory  - deleting ****\n" && \
        rm -rf ./build
