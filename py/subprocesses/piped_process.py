#!/usr/bin/env python
import subprocess

# decode bytes to string


def decoder(x): return x.decode('UTF-8')


# the file where command output will be saved
output_file = 'results.out'


class Piped_Process:

    def __init__(self, command_list):
        if(len(command_list) == 1):
            self.piped_command = f'{command_list[0]}'
        else:
            self.piped_command = Piped_Process.Generate_Pipe(command_list)

    @classmethod
    def Generate_Pipe(cls, command_list):
        piped_command = f''
        cmd_idx = 0
        for cmd in command_list:
            if(cmd_idx == 0):
                piped_command = cmd
            else:
                piped_command = piped_command + ' | ' + cmd
            cmd_idx += 1
        return piped_command

    @classmethod
    def Run_Process(cls, proc_list):
        """Execute a piped command after each argument has been properly added in the piped instruction
        Returns the output and the error of the executed command
        """

        piped_process = Piped_Process(proc_list).piped_command
        process = subprocess.Popen(piped_process, shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        try:
            process_output = process.stdout.read()
            process_error = process.stderr.read()
        except Exception as exc:
            print(
                f'Issue while running process within the script...\nReason{exc}')
            process.kill()
        return process_output, process_error

    @classmethod
    def Get_Process_Output(cls, proc_list):
        piped_process = Piped_Process.Generate_Pipe(proc_list)
        process = subprocess.Popen(piped_process, shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, errors = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, errors = process.communicate()
        return output, errors

    @classmethod
    def Save_Process_Output(cls, proc_list, output_file):
        new_proc_list = Piped_Process.Generate_Command_List(
            'python', proc_list)
        process = Piped_Process.Get_Process_Output(new_proc_list)
        process_output = process[0]
        process_error = process[1]
        if(process_error == b''):
            return_code = 1
        else:
            return_code = -1
        if(return_code == 1):
            decoded_output = decoder(process_output)
        with open(output_file, 'w+') as saver:
            try:
                saver.write(decoded_output)
            except Exception as err:
                print(f'Could not write to the file...\nReason: {err}')
                return -1

    @classmethod
    def Generate_Command_List(cls, process, command_list):
        grep_process = f'grep {process}'
        new_command_list = command_list
        new_command_list.insert(1, grep_process)
        return new_command_list


command_list = ['ps aux', 'awk \'{print $2,$11}\'']

process_list = ['logstash', 'ssh', 'python', 'bash']

initial_list = command_list


if(__name__ == '__main__'):
    Piped_Process.Save_Process_Output(command_list, output_file)