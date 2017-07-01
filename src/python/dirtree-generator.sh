#!/usr/bin/env bash


function print_help {
    usage="$(basename "$0") [-m] [-h] [-v] DIRPATH

Simple script that generates or modifies testing file tree for myscm-srv
application tests.

This script creates testing file tree in DIRPATH directory unless -m flag is
present which indicates that existing simple file tree in DIRPATH directory
will be modified in some specific manner described in the project's white
paper's appendix.

DIRPATH is absolute or relative path to directory where testing file tree will
be saved or will be modified if -m option is present. If -m option is not
present, then all of the non-existing parent directories in DIRPATH path will
be created unless they already exist (using 'mkdir -p' command).

To test process of generating system images by myscm-srv you can follow these
steps:
  1. create sample testing file tree using this script,
  2. scan testing file tree using myscm-srv application,
  3. make sample changes using this script,
  4. scan testing file tree again and create system image using myscm-srv.

Options:
    -m                  make sample, testing changes in DIRPATH directory
    -h                  show this help text
    -v                  increase verbosity and print all of the commands
                        that are ran to create or to change (if -m option is
                        present) sample testing file tree in DIRPATH"
    echo "$usage" >&2
    exit
}


echo_verbose () {
    if [ $verbose -gt 0 ]; then
        echo "$@"
    fi
}


# https://stackoverflow.com/a/5195741/1321680
myassert () {
    echo_verbose " $ $@"
    "$@"
    local status=$?

    if [ $status -ne 0 ]; then
        echo "Command '$@' returned error $1. Exiting without cleaning up '$output_dirpath'!" >& 2
        exit
    fi
}


generate_sample_dirtree () {
    echo_verbose "Creating file tree in '$output_dirpath'..."

    myassert mkdir -p "$output_dirpath"
    myassert cd "$output_dirpath"
    myassert echo '0th file' > file0
    myassert echo '1st file' > file1
    myassert mkdir dir{0..3} dir1/subdir{0..3}
    myassert ln -s file1 file1_symlink
    myassert ln -s dir3 dir3_symlink
    myassert touch dir1/file
    myassert echo '2nd file' > dir1/file2
    myassert echo '3rd file' > dir1/file3
    myassert echo '4th file' > dir1/subdir1/file4
    myassert echo '5th file' > dir1/subdir1/file5
    myassert echo '6th file' > dir1/subdir2/file6
    myassert echo '7th file' > dir1/subdir2/file7
    myassert mkfifo dir2/fifo{0,1}
    myassert echo '8th file' > dir3/file8
    myassert echo '9th file' > dir3/file9
    myassert ln dir3/file8 file8_hardlink
    myassert chmod 777 dir1/file2
    myassert ln dir1/subdir1/file4 file4_hardlink
    myassert chgrp wireshark dir1/file3

    echo_verbose "Creating sample file tree '$output_dirpath' ended successfully!"
}


assert_expected_dirtree () {
    echo_verbose "Checking if the content of the '$output_dirpath' directory is identical to the expected one..."

    expected_dir_content=". ./dir0 ./dir1 ./dir1/file ./dir1/file2 ./dir1/file3 ./dir1/subdir0 ./dir1/subdir1 ./dir1/subdir1/file4 ./dir1/subdir1/file5 ./dir1/subdir2 ./dir1/subdir2/file6 ./dir1/subdir2/file7 ./dir1/subdir3 ./dir2 ./dir2/fifo0 ./dir2/fifo1 ./dir3 ./dir3/file8 ./dir3/file9 ./dir3_symlink ./file0 ./file1 ./file1_symlink ./file4_hardlink ./file8_hardlink"

    myassert cd "$output_dirpath"
    actual_dir_content="$(timeout -k 5s 3s find . -print 2> /dev/null | sort | xargs echo)"

    if [ "$?" -eq 0 ] && [ "$expected_dir_content" ==  "$actual_dir_content" ]; then
        echo_verbose "Content of the '$output_dirpath' directory is OK"
        return 0
    else
        echo_verbose "Unexpected content of the '$output_dirpath' directory" >& 2
        return 1
    fi
}


modify_sample_dirtree () {
    echo_verbose "Modifying directory '$output_dirpath'..."

    myassert cd "$output_dirpath"
    myassert mv dir2/fifo0 dir0
    myassert echo 'x' >> file1
    myassert rm file8_hardlink dir1/subdir1/file4
    myassert mv dir3/file9 .
    myassert chmod o-rwx dir1/file2
    myassert chgrp audio dir1/file3
    myassert mv file0 file0_renamed
    myassert ln -s dir1/subdir2/file6 file6_symlink
    myassert ln dir1/subdir2/file7 file7_hardlink
    myassert touch dir1/subdir1/file5

    echo_verbose "Modifying directory '$output_dirpath' ended successfully!"
}


verbose=0
modify_dirtree=0
output_dirpath=""

while getopts ':mhv' opt; do
    case "$opt" in
    m)  modify_dirtree=1
        ;;
    h)
        print_help
        ;;
    v)  verbose=1
        ;;
    :)  printf "Missing argument for -%s\n" "$OPTARG" >&2
        print_help
        ;;
    \?) printf "Illegal option: -%s\n" "$OPTARG" >&2
        print_help
       ;;
   esac
done

shift $((OPTIND - 1))
[ "$1" = "--" ] && shift

if [ ! $# -eq 1 ]; then
    print_help
fi

output_dirpath=$1

if [ "$modify_dirtree" -eq 1 ]; then
    if [ ! -d "$output_dirpath" ]; then
        echo "'$output_dirpath' doesn't exist - specify path of the existing testing file tree created by this program" >& 2
    elif assert_expected_dirtree; then
        modify_sample_dirtree
    else
        echo "Given directory '$output_dirpath' is not identical to one created with this tool, thus cannot be modified" >& 2
    fi
else
    if [ -d "$output_dirpath" ]; then
        echo "'$output_dirpath' already exists - specify non-existing directory path" >& 2
    else
        generate_sample_dirtree
    fi
fi
