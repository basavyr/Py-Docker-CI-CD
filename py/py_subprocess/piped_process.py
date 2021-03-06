#!/usr/bin/env python
import subprocess
import os
import time


# decode bytes to string
def decoder(x): return x.decode('UTF-8')


# shows the current time usinng the daetime module
def now(): return time.time()


class Process:

    # the command which will be used for checking if a certain process/service is running on the system or not
    command_list = ['ps aux', 'awk \'{print $2,$11,$12}\'']

    # def __init__(self, command_list):
    #     if(len(command_list) == 1):
    #         self.piped_command = f'{command_list[0]}'
    #     else:
    #         self.piped_command = Process.Generate_Pipe(command_list)

    @classmethod
    def Generate_Piped_Command(cls, command_list):
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
    def Generate_Grepped_Command(cls, process, command_list):
        grepped_process = f'grep {process}'
        new_command_list = list(command_list)
        new_command_list.insert(1, grepped_process)
        return new_command_list

    @classmethod
    def Create_Full_Command(cls, process, command_list):
        grepped_command = Process.Generate_Grepped_Command(
            process, command_list)
        piped_command = Process.Generate_Piped_Command(grepped_command)
        return piped_command

    @classmethod
    def Count_Running_Instances(cls, process):
        """
        Count the number of running instances for a given process
        """
        process_path = f'{Register.register_directory_name}/{process}.list'
        try:
            with open(process_path, 'r+') as process_reader:
                lines = process_reader.readlines()
        except FileNotFoundError:
            return -1

        # when the script is running from the command line, the shell comands given in the script are executed within the python module -> this introduces the spawn of /bin/sh
        # the grep command which is executed from within python will also count as a command within each process register file
        # thus, the overall overhead of two extra commands must be subtracted from each register file
        return len(lines) - 2

    @classmethod
    def Process_Instance_Behavior(cls, process, instance_number):
        if(instance_number < 0):
            print(
                f'there are stopped instances for {process}...Will raise alert')
        elif (instance_number == 0):
            print(f'{process} does not have modified instances...')
        else:
            print(f'{process} has increased instances with normal behavior...')

    @classmethod
    def Analyze_Process_Stack(cls, process_list, running_instances, process_stack):
        """
        Determines if a process has changed its number of running instances


        The method goes through each process separately, it creates a tuple with the process name and the process stack

        The process stack shows the difference between the current active instances of a process and the active instances which were running during the previous iteration
        """

        debug_mode = False

        if(debug_mode):
            print(f'will perform analysis on the instance stack')

        idx = 0

        # assume there are no changes within the active instances for each process
        unchanged_instances = False

        if(any(process_stack)):
            if(debug_mode):
                print('there are changes within active instances')
            unchanged_instances = True
        else:
            if(debug_mode):
                print('there are no changes in the active instances')
            pass

        if(unchanged_instances == False):
            if(debug_mode):
                print('no changes in the running instances. aborting...')
            return

        if(debug_mode):
            print('continue analysis [no_abort]')

        for process in zip(process_list, process_stack):
            p_name = process[0]
            p_instances = process[1]
            if(p_instances == 0):
                if(debug_mode):
                    print(
                        f'{p_name} has no changes within its active instances...')  # ! the p_instances null does not mean that there are no running instances
                continue
            else:
                if(p_instances > 0):
                    # depending on wether the value of the process stack is positive or negative, show proper output to the screen
                    initial_instances = running_instances[idx] - p_instances
                    current_instances = running_instances[idx]
                    print(
                        f'Change for [{p_name}] -> from ({initial_instances}) to ({current_instances}) instances')
                elif(p_instances < 0):
                    # depending on wether the value of the process stack is positive or negative, show proper output to the screen
                    initial_instances = running_instances[idx] - p_instances
                    current_instances = running_instances[idx]
                    print(
                        f'Change for [{p_name}] -> from ({initial_instances}) to ({current_instances}) instances')

                # if(debug_mode):
                #     print(
                #         f'{p_name} had {initial_instances} and now it has {current_instances}')

                Process.Process_Instance_Behavior(p_name, p_instances)
                # if(p_instances < 0):
                #     print(
                #         f'({abs(p_instances)}) [{p_name}] instances stopped running...')
                # elif(p_instances > 0):
                #     print(
                #         f'({abs(p_instances)}) new [{p_name}] instances started running...')
            idx += 1


class Register:

    register_directory_name = 'register'

    @ classmethod
    def Create_Register_Directory(cls, register_name):
        try:
            os.mkdir(register_name)
        except FileExistsError:
            # print(f'Could not make directory.\nReason: {err}')
            pass
        return

    @ classmethod
    def Create_File_Register(cls, proc_name, command_list):
        debug_mode = 0

        # generate the path where all the running instances will be saved
        if(debug_mode):
            print('Creating the proper path to the process list file')
        file_name = f'{Register.register_directory_name}/{proc_name}.list'

        # with the path to the file active
        # generates the command that will be executed
        if(debug_mode):
            print(
                'Generating the proper command that has to be executed within the CLI for the current process')
        full_command = Process.Create_Full_Command(
            proc_name, command_list)
        if(debug_mode):
            print(f'Full command: {full_command}')

        with open(file_name, 'w+'):
            try:
                Process.Save_Process_Output(
                    full_command, file_name)
            except Exception as exc:
                print(f'Error: {exc}')

    @ classmethod
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


class Utils():
    """Functions and implementations that are used for monitoring running processes

    All the occuring instances within the process tree are monitored
    """

    process_table = 'process.table'

    @classmethod
    def Watch_Process_Register(cls, register, execution_time):
        # set true for console print
        debug_mode = False

        # set true for monitoring
        runtime = True

        # avoid any instance counting during the first run of the script
        dry_run = 1

        start_time = time.time()
        if(runtime):
            print(f'Monitoring -> {register}\n')

        # the time after which another monitoring iteration is started
        refresh_time = 5

        current_instance_number = [0 for _ in register]
        last_instance_number = [0 for _ in register]

        itx = 1
        # start the monitoring process
        while(runtime and now() - start_time < execution_time):
            # if(debug_mode):
            print(f'Iteration {itx}...')

            # create a file register where all running instances for each process within the process list will be saved
            for process in register:
                Register.Create_File_Register(process, Process.command_list)

            # count the running instances of all processes
            current_instance_number = [Process.Count_Running_Instances(
                process) for process in register]
            if(debug_mode):
                print(
                    f'The current instances for all processes:\n{current_instance_number}')
            if(debug_mode and dry_run == 0):
                if(debug_mode):
                    print(
                        f'The current process stack: {current_instance_number}')
                pass

            # calculate the difference between the previous instance stack and the current instance stack for all processes
            if(dry_run == 0):
                diffs = [current_instance_number[idx] - last_instance_number[idx]
                         for idx in range(len(register))]

            if(itx > 1 and dry_run == 0):
                if(debug_mode):
                    print(
                        f'Analyzing the instance stack\nChanges in instances {diffs}')
                Process.Analyze_Process_Stack(
                    register, current_instance_number, diffs)

            if(debug_mode):
                print(
                    f'The last instances for each process:\n{last_instance_number}')
            last_instance_number = list(current_instance_number)

            itx += 1
            dry_run = 0
            time.sleep(refresh_time)
        print('Finished monitoring the process register')

    @ classmethod
    def Pull_Processes(cls, process_table):
        try:
            with open(process_table, 'r+') as table:
                process_list = table.readlines()
        except FileNotFoundError:
            return -1

        # clean the list
        cleaned_list = [str(x).strip() for x in process_list]
        return cleaned_list


if(__name__ == '__main__'):

    # creating the directory where each instance of a process will be saved as a file
    Register.Create_Register_Directory(Register.register_directory_name)

    # clean up the register files after the monitoring tool has finished its pipeline
    clean_up = True

    # total runtie of the monitoring tool
    EXECUTION_TIME = 40

    runtime = True

    try:
        REGISTER = Utils.Pull_Processes(Utils.process_table)
        assert REGISTER != -1, 'Process table missing. Cannot start the monitoring process'
    except AssertionError:
        runtime = False
    else:
        pass

    if(runtime):
        Utils.Watch_Process_Register(REGISTER, EXECUTION_TIME)
    else:
        print('Could not start the monitoring process due to missing process table.')

    if(clean_up and runtime):
        print('Doing registry cleanup')
        # cleaning up the register
        # removing the files in which all running processes are stored
        Register.Clean_Register_Directory()
