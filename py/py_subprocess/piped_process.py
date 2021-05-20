#!/usr/bin/env python
import subprocess
import os
import time


# decode bytes to string
def decoder(x): return x.decode('UTF-8')


class Process:

    # the command which will be used for checking if a certain process/service is running on the system or not
    process_getter_command = ['ps aux', 'awk \'{print $2,$11,$12}\'']

    # def __init__(self, command_list):
    #     if(len(command_list) == 1):
    #         self.piped_command = f'{command_list[0]}'
    #     else:
    #         self.piped_command = Process.Generate_Pipe(command_list)

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
    def Run_Process(cls, piped_command):
        """Execute a piped command after each argument has been properly added in the piped instruction
        Returns the output and the error of the executed command
        """
        process = subprocess.Popen(piped_command, shell=True,
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
    def Get_Process_Output(cls, piped_command):
        process = subprocess.Popen(piped_command, shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, errors = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, errors = process.communicate()
        return output, errors

    @classmethod
    def Save_Process_Output(cls, piped_command, output_file):
        # execute the process and retrieve its output from the console
        process = Process.Get_Process_Output(piped_command)

        process_output = process[0]
        process_error = process[1]

        decoded_output = ''
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
        new_command_list = list(command_list)
        new_command_list.insert(1, grep_process)
        return new_command_list

    @classmethod
    def Create_Process_Register(cls, process, command_list):
        new_command_list = Process.Generate_Command_List(
            process, command_list)
        grepped_command = Process.Generate_Pipe(new_command_list)
        return grepped_command


class Register:

    register_directory_name = 'register'

    @classmethod
    def Create_Register_Directory(cls, register_name):
        try:
            os.mkdir(register_name)
        except FileExistsError:
            # print(f'Could not make directory.\nReason: {err}')
            pass
        return

    @classmethod
    def Create_File_Register(cls, proc_name, command_list):
        debug_moode = 0

        if(debug_moode):
            print('Creating the proper path to the process list file')
        file_name = f'{Register.register_directory_name}/{proc_name}.list'
        full_command = Process.Create_Process_Register(
            proc_name, command_list)
        if(debug_moode):
            print(f'Full command: {full_command}')
        with open(file_name, 'w+'):
            try:
                Process.Save_Process_Output(
                    full_command, file_name)
            except Exception as exc:
                print(f'Error: {exc}')

    @classmethod
    def Clean_Register_Directory(cls):
        dirr = Register.register_directory_name
        if(os.path.isdir(dirr)):
            files = os.listdir(dirr)
            if(len(files) > 0):
                for file in files:
                    try:
                        os.remove(
                            f'{Register.register_directory_name}/{os.path.relpath(file)}')
                    except Exception as err:
                        print(
                            f'Could not remove the file from the process register!\nReason: {err}')
                # print('Process register empty. Skipping the cleaning procedure')
                pass


process_list = ['logstash', 'ssh', 'python', 'bash', 'code']


if(__name__ == '__main__'):
    # creating the directory where each instance of a process will be saved as a file
    Register.Create_Register_Directory(Register.register_directory_name)

    runtime = True
    clean_up = False

    total_execution_time = 5

    itx = 1
    print(f'Starting iterations...')

    start_time = time.time()
    while(runtime):
        print(f'Iteration {itx}...')
        for monitored_process in process_list:
            Register.Create_File_Register(
                monitored_process, Process.process_getter_command)
        if(int(time.time() - start_time) < total_execution_time):
            time.sleep(1)
        else:
            runtime = False
        itx += 1

    if(clean_up):
        print('Doing cleanup')
        # cleaning up the register
        # removing the files in which all running processes are stored
        Register.Clean_Register_Directory()