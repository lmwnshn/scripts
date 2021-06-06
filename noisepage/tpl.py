'''
Navigating the NoisePage execution engine drives me nuts.
Run this in CLion terminal and you can click on the links.

Typical use:
  python3 tpl.py -h
'''

import argparse
import os


PROJECT_ROOT = r'/home/kapi/CLionProjects/noisepage/'


def extract_f_args(sym, filepath):
    F_INVALID = 0
    F_NEXT_ARG = 1
    F_NEXT_LINE = 2
    F_FINISH = 3

    def next_f(s):
        idx, f = s.find(','), F_NEXT_ARG
        if idx == -1:
            idx, f = s.find(')'), F_FINISH
        if idx == -1:
            idx, f = s.find('\\'), F_NEXT_LINE
        if idx == -1:
            f = F_INVALID
        return idx, f

    start, lines, args = 0, [], []
    f = F_INVALID
    for linenum, line in enumerate(open(filepath), 1):
        if sym in line:
            lines.append(line.rstrip())
            start = linenum
            f = F_NEXT_ARG
            line = line[line.find(sym):].strip()

        if f == F_NEXT_LINE:
            lines.append(line.rstrip())
            f = F_NEXT_ARG
        elif f == F_FINISH:
            break

        while f == F_NEXT_ARG:
            idx, f = next_f(line)
            args.append(line[:idx])
            line = line[idx + 1:]
    return {'start': start, 'lines': lines, 'args': args}


def extract_check_call(main_check_name, builtin_name, filepath):
    start, lines = 0, []

    in1, in2, in3 = False, False, False
    for linenum, line in enumerate(open(filepath), 1):
        if not in1 and main_check_name in line:
            in1 = True
        elif not in2 and in1 and builtin_name in line:
            in2 = True
            start = linenum
            lines.append(line.rstrip())
            if '{' in line:
                in3 = True
        elif not in3 and in2 and '{' in line:
            in3 = True
        elif in3:
            if '}' in line:
                break
            else:
                lines.append(line.rstrip())
    return start, lines


def extract_function(func, filepath):
    start, lines = 0, []

    cnt, in_def, seen_brace, seen_semicolon = 0, False, False, False
    for linenum, line in enumerate(open(filepath), 1):
        if in_def:
            s = line.rstrip()
            lines.append(s)
            cnt = cnt + s.count('{') - s.count('}')
            if '{' in s:
                seen_brace = True
            if ';' in s:
                seen_semicolon = True
        elif func in line:
            in_def = True
            start = linenum
            s = line.rstrip()
            lines.append(s)
            cnt = cnt + s.count('{') - s.count('}')
            if '{' in line:
                seen_brace = True
            if ';' in line:
                seen_semicolon = True
        if seen_semicolon and not seen_brace:
            break
        if len(lines) > 0 and cnt == 0 and seen_brace:
            break
    return start, lines


def extract_builtins_h(builtin_name):
    relpath = 'src/include/execution/ast/builtins.h'
    filepath = os.path.join(PROJECT_ROOT, relpath)
    f_args = extract_f_args('{},'.format(builtin_name), filepath)
    internal_name = f_args['args'][0]
    function_name = f_args['args'][1]
    return filepath, f_args


def extract_sema_builtin_cpp_1(builtin_name):
    relpath = 'src/execution/sema/sema_builtin.cpp'
    filepath = os.path.join(PROJECT_ROOT, relpath)

    maincheck = 'Sema::CheckBuiltinCall'
    start, lines = extract_check_call(maincheck, builtin_name, filepath)

    return filepath, {'start': start, 'lines': lines}


def extract_sema_builtin_cpp_2(info):
    relpath = 'src/execution/sema/sema_builtin.cpp'
    filepath = os.path.join(PROJECT_ROOT, relpath)

    for line in info['lines']:
        if 'Check' in line:
            func = line[line.find('Check'):line.find('(')]
            break
    start, lines = extract_function('Sema::{}'.format(func), filepath)

    return filepath, {'start': start, 'lines': lines}


def extract_bytecode_generator_cpp_1(builtin_name):
    relpath = 'src/execution/vm/bytecode_generator.cpp'
    filepath = os.path.join(PROJECT_ROOT, relpath)

    maincheck = 'BytecodeGenerator::VisitBuiltinCallExpr'
    start, lines = extract_check_call(maincheck, builtin_name, filepath)

    return filepath, {'start': start, 'lines': lines}


def extract_bytecode_generator_cpp_2(info):
    relpath = 'src/execution/vm/bytecode_generator.cpp'
    filepath = os.path.join(PROJECT_ROOT, relpath)

    for line in info['lines']:
        if 'Visit' in line:
            func = line[line.find('Visit'):line.find('(')]
            break
    start, lines = \
        extract_function('BytecodeGenerator::{}('.format(func), filepath)

    return filepath, {'start': start, 'lines': lines}


def extract_bytecodes_h(bytecode_name):
    relpath = 'src/include/execution/vm/bytecodes.h'
    filepath = os.path.join(PROJECT_ROOT, relpath)
    f_args = extract_f_args('{},'.format(bytecode_name), filepath)
    return filepath, f_args


def extract_vm_cpp(bytecode_name):
    relpath = 'src/execution/vm/vm.cpp'
    filepath = os.path.join(PROJECT_ROOT, relpath)
    start, lines = \
        extract_function('OP({}) : '.format(bytecode_name), filepath)
    return filepath, {'start': start, 'lines': lines}


def extract_bytecode_handlers_h(bytecode_name):
    relpath = 'src/include/execution/vm/bytecode_handlers.h'
    filepath = os.path.join(PROJECT_ROOT, relpath)
    start, lines = extract_function('Op{}('.format(bytecode_name), filepath)
    return filepath, {'start': start, 'lines': lines}


def print_lines(final, module, truncate_after=3):
    for filepath in final[module]:
        print('{}:{}'.format(filepath, final[module][filepath]['start']))
        for i, line in enumerate(final[module][filepath]['lines']):
            print(line)
            if i >= truncate_after:
                print('<TRUNCATED>')
                break


def main():
    parser = argparse.ArgumentParser(
        description='Navigate the NoisePage execution engine.')
    parser.add_argument('-p', '--builtin', help='Builtin name.')
    parser.add_argument('-q', '--bytecode', help='Bytecode name.')
    parser.add_argument('-b', '--both', help='Builtin and bytecode name.')
    args = parser.parse_args()

    final = {}
    final['builtins'] = {}
    final['sema_builtin_1'] = {}
    final['sema_builtin_2'] = {}
    final['bytecode_generator_1'] = {}
    final['bytecode_generator_2'] = {}
    final['bytecodes'] = {}
    final['vm'] = {}
    final['bytecode_handlers'] = {}

    if args.both:
        args.builtin = args.both
        args.bytecode = args.both

    if args.builtin:
        builtin_name = args.builtin

        # ast/builtins.h
        filepath, f_args = extract_builtins_h(builtin_name)
        final['builtins'][filepath] = f_args
        # sema/sema_builtin.cpp
        filepath, info = extract_sema_builtin_cpp_1(builtin_name)
        final['sema_builtin_1'][filepath] = info
        filepath, info = extract_sema_builtin_cpp_2(info)
        final['sema_builtin_2'][filepath] = info
        # vm/bytecode_generator.cpp
        filepath, info = extract_bytecode_generator_cpp_1(builtin_name)
        final['bytecode_generator_1'][filepath] = info
        filepath, info = extract_bytecode_generator_cpp_2(info)
        final['bytecode_generator_2'][filepath] = info

    if args.bytecode:
        bytecode = args.bytecode
        # vm/bytecodes.h
        filepath, f_args = extract_bytecodes_h(bytecode)
        final['bytecodes'][filepath] = f_args
        # vm/vm.cpp
        filepath, info = extract_vm_cpp(bytecode)
        final['vm'][filepath] = info
        # vm/bytecode_handlers.h
        filepath, info = extract_bytecode_handlers_h(bytecode)
        final['bytecode_handlers'][filepath] = info

    print()
    print('Source Code')
    print('===========')

    print_lines(final, 'builtins')
    print_lines(final, 'sema_builtin_1')
    print_lines(final, 'sema_builtin_2')
    print_lines(final, 'bytecode_generator_1')
    print_lines(final, 'bytecode_generator_2')
    print_lines(final, 'bytecodes')
    print_lines(final, 'vm')
    print_lines(final, 'bytecode_handlers')


if __name__ == '__main__':
    main()
