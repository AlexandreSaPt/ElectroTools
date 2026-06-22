import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import math
import sys
import signal

plt.ion()  # 1. Turn on interactive mode (non-blocking)

def calculate_ntc_resistance(temp_list, beta, r_ref, t_ref, celsius=True):
    t_ref_k = t_ref + 273.15 if celsius else t_ref
    resistance_list = []
    for t in temp_list:
        t_k = t + 273.15 if celsius else t
        r = r_ref * math.exp(beta * ((1.0 / t_k) - (1.0 / t_ref_k)))
        resistance_list.append(r)
    return resistance_list


def calculate_res_div(r_list, r1, vdd):
    return [vdd * (r / (r + r1)) for r in r_list]

def calculate_voltage_adc(v_list, adc_lsb_voltage):
    return [round(v / adc_lsb_voltage) * adc_lsb_voltage for v in v_list]

def calculate_r_ntc_from_voltage(v_list, r1, vdd):
    r_ntc_list = []
    for v in v_list:
        r_ntc = (v * (r1 + vdd)) / (vdd - v) if vdd != v else float('inf')
        r_ntc_list.append(r_ntc)
    return r_ntc_list

def calculate_temperature_from_r_ntc(r_list, beta, r_ref, t_ref, celsius=True):
    t_ref_k = t_ref + 273.15 if celsius else t_ref
    temperature_list = []
    for r in r_list:
        if r <= 0:
            temperature_list.append(float('nan'))
            continue
        t_k = 1.0 / ((1.0 / beta) * math.log(r / r_ref) + (1.0 / t_ref_k))
        temperature_list.append(t_k - 273.15 if celsius else t_k)
    return temperature_list


def calculate_derivative(x_list, y_list):
    n = len(x_list)
    if n != len(y_list):
        raise ValueError("x_list and y_list must have the same length.")
    if n < 2:
        raise ValueError("At least two points are required to calculate a derivative.")
    dy_dx = []
    for i in range(n):
        if i == 0:
            slope = (y_list[1] - y_list[0]) / (x_list[1] - x_list[0])
        elif i == n - 1:
            slope = (y_list[n-1] - y_list[n-2]) / (x_list[n-1] - x_list[n-2])
        else:
            slope = (y_list[i+1] - y_list[i-1]) / (x_list[i+1] - x_list[i-1])
        dy_dx.append(slope)
    return dy_dx


def generate_full_e12_series():
    base_values = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    full_series = []
    for decade in range(3, 6): #1000 - 10000
        multiplier = 10 ** decade
        for base in base_values:
            val = round(base * multiplier, 2)
            full_series.append(val)
    return full_series


def generate_plot(x_label, x_data, y_datasets, title):
    fig, ax = plt.subplots(figsize=(10, 5))
    lines = []
    for label, y in y_datasets:
        line, = ax.plot(x_data, y, label=label, linewidth=2)
        lines.append(line)
    ax.set_xlabel(x_label)
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    return fig, ax, lines


def annotate_point(ax, x, y, text):
    ax.plot([x], [y], marker='o', color='red')
    ax.annotate(text, xy=(x, y), xytext=(10, 10), textcoords='offset points', bbox=dict(boxstyle='round', fc='w'))



def prompt_value(prompt_text, cast_func, default):
    while True:
        try:
            raw = input(f"{prompt_text} [{default}]: ")
        except EOFError:
            raw = ''
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting.")
            plt.close('all')
            sys.exit(0)
        if raw.strip() == '':
            return default
        try:
            return cast_func(raw)
        except Exception:
            print("Invalid input, try again.")


def run_derivative_analysis(r_ref, temp_ref, beta, vdd, temperature_list, all_e12_resistors, idx_target, temp_target):
    """Run the derivative-based selection analysis and display plots."""
    v_deriv_min_list = []
    r_ntc = calculate_ntc_resistance(temperature_list, beta, r_ref, temp_ref)

    for r1 in all_e12_resistors:
        v_ntc = calculate_res_div(r_ntc, r1, vdd)
        v_deriv = calculate_derivative(temperature_list, v_ntc)
        v_deriv_min_list.append(v_deriv[idx_target])

    best_idx = int(np.argmin(v_deriv_min_list))
    best_r1 = all_e12_resistors[best_idx]
    print(f"Best R1 option is {best_r1} Ohms (derivative={v_deriv_min_list[best_idx]:.6g})")

    fig, ax, _ = generate_plot(
        x_label='R1 (Ohms)',
        x_data=all_e12_resistors,
        y_datasets=[['V derivative', v_deriv_min_list]],
        title=f'Derivative vs R1 for {temp_target}ºC'
    )

    annotate_point(ax, best_r1, v_deriv_min_list[best_idx], f'Min: {best_r1}Ω\n{v_deriv_min_list[best_idx]:.4g}')

    x_arr = np.array(all_e12_resistors)
    y_arr = np.array(v_deriv_min_list)
    def on_click(event):
        if event.inaxes != ax:
            return
        x_click = event.xdata
        idx = int(np.argmin(np.abs(x_arr - x_click)))
        x_val = x_arr[idx]
        y_val = y_arr[idx]
        ax.lines = [ln for ln in ax.lines if ln.get_label() != '_annot_']
        ax.collections.clear()
        annotate_point(ax, x_val, y_val, f'{int(x_val)}Ω, {y_val:.4g}')
        fig.canvas.draw()


def run_worst_case_analysis(r_ref, temp_ref, beta, beta_percentage_tol, vdd, temperature_list, all_e12_resistors, temp_target, adc_lsb_voltage, r1_percentage_tol):
    """Run worst-case error analysis and display diagnostic plots."""
    best_r1 = run_derivative_analysis(r_ref, temp_ref, beta, vdd, temperature_list, all_e12_resistors, temperature_list.index(temp_target), temp_target)

    max_error = []
    max_error_at_target = []
    for r in all_e12_resistors:
        worst_case_error = calculate_worst_case_voltage_error(
            r_ref, temp_ref, beta, beta_percentage_tol, vdd, temperature_list, adc_lsb_voltage, r1_percentage_tol, r
        )
        max_error.append(max(worst_case_error))
        max_error_at_target.append(worst_case_error[temperature_list.index(temp_target)])

    generate_plot(
        "R1 (Ohms)",
        all_e12_resistors,
        [["Max worst case voltage error", max_error]],
        "Max worst case voltage error vs R1 for any temperature"
    )
    generate_plot(
        "R1 (Ohms)",
        all_e12_resistors,
        [["Max worst case voltage error at target", max_error_at_target]],
        f"Max worst case voltage error vs R1 for {temp_target}ºC"
    )
    return best_r1


def calculate_r_ntc_worst_cases(r_ref, temp_ref, beta, beta_percentage_tol, temperature_list):
    r_ntc_max = calculate_ntc_resistance(temperature_list, beta + beta_percentage_tol * beta / 100.0, r_ref, temp_ref)
    r_ntc_min = calculate_ntc_resistance(temperature_list, beta - beta_percentage_tol * beta / 100.0, r_ref, temp_ref)
    return [r_ntc_min, r_ntc_max]

def calculate_voltage_worst_cases(r_ntc_list, r1, vdd, r1_percentage_tol):
    v_ntc_cases = []
    #for each in list
    for r_ntc in r_ntc_list:
        if len(r_ntc) != len(r_ntc_list[0]):
            raise ValueError("All r_ntc lists must have the same length.")
        v_ntc_min = calculate_res_div(r_ntc, r1 * (1 - r1_percentage_tol / 100.0), vdd)
        v_ntc_max = calculate_res_div(r_ntc, r1 * (1 + r1_percentage_tol / 100.0), vdd)

        v_ntc_cases.append(v_ntc_min)
        v_ntc_cases.append(v_ntc_max)

    return v_ntc_cases

def calculate_voltage_adc_worst_cases(v_ntc_worst_cases, adc_lsb_voltage):
    v_adc_worst_cases = []
    for v_list in v_ntc_worst_cases:
        v_adc = calculate_voltage_adc(v_list, adc_lsb_voltage)
        v_adc_worst_cases.append(v_adc)
    return v_adc_worst_cases

def calculate_r_ntc_from_voltage_worst_cases(v_adc_worst_cases, r1, vdd):
    r_ntc_worst_cases = []
    for v_list in v_adc_worst_cases:
        r_ntc = calculate_r_ntc_from_voltage(v_list, r1, vdd)
        r_ntc_worst_cases.append(r_ntc)
    return r_ntc_worst_cases

def calculate_temperature_from_r_ntc_worst_cases(r_ntc_worst_cases, beta, r_ref, temp_ref):
    temperature_worst_cases = []
    for r_list in r_ntc_worst_cases:
        temp_list = calculate_temperature_from_r_ntc(r_list, beta, r_ref, temp_ref)
        temperature_worst_cases.append(temp_list)
    return temperature_worst_cases

def calculate_temperature_error_worst_cases(temperature_worst_cases, temperature_list):
    error_worst_cases = []
    for temp_list in temperature_worst_cases:
        error_list = [abs(t - t_ref) for t, t_ref in zip(temp_list, temperature_list)]
        error_worst_cases.append(error_list)
    return error_worst_cases

def calculate_max_temperature_error_from_tolerances(r_ref, temp_ref, beta, beta_percentage_tol, vdd, temperature_list, adc_lsb_voltage, r1_percentage_tol, r1):
    print(f"R1 value: {r1} Ohms")
    """Compute the maximum temperature error from NTC and R1 tolerances."""
    r_ntc_worst_cases = calculate_r_ntc_worst_cases(r_ref, temp_ref, beta, beta_percentage_tol, temperature_list) # R_ntc (temperature) with NTC tolerance applied
    v_ntc_worst_cases = calculate_voltage_worst_cases(r_ntc_worst_cases, r1, vdd, r1_percentage_tol) # V_ntc (temperature) with NTC and R1 tolerances applied
    v_adc_worst_cases = calculate_voltage_adc_worst_cases(v_ntc_worst_cases, adc_lsb_voltage) # V_adc (temperature) with NTC and R1 tolerances applied and ADC quantization applied
    r_ntc_from_v_worst_cases = calculate_r_ntc_from_voltage_worst_cases(v_adc_worst_cases, r1, vdd) # this is what is calculated from the ADC readings and computed in the MCU assuming that everything is ideal
    temperature_from_r_worst_cases = calculate_temperature_from_r_ntc_worst_cases(r_ntc_from_v_worst_cases, beta, r_ref, temp_ref) # this is the temperature that the MCU sees Temperature_MCU (Temperature)
    error_from_tolerances = calculate_temperature_error_worst_cases(temperature_from_r_worst_cases, temperature_list)

    #USE GENERATE PLOT TO GENERATE A PLOT of error_from_tolerances
    '''
    dataset=[]
    for i, error in enumerate(error_from_tolerances):
        dataset.append([f'Error case {i+1}', error])

    generate_plot(
        "Temperature (°C)",
        temperature_list,
        dataset,
        "Temperature error vs Temperature for worst-case tolerances"
    )
    '''

    return error_from_tolerances

def calculate_single_list_of_max_temperature_errors(error_from_tolerances):
    max_error = []
    for i in range(len(error_from_tolerances[0])):
        max_error.append(max(error[i] for error in error_from_tolerances))
    return max_error


def calculate_worst_case_voltage_error(r_ref, temp_ref, beta, beta_percentage_tol, vdd, temperature_list, adc_lsb_voltage, r1_percentage_tol, best_r1):
    """Compute worst-case voltage error using NTC and R1 tolerances."""
    v_ntc_ideal = calculate_res_div(calculate_ntc_resistance(temperature_list, beta, r_ref, temp_ref), best_r1, vdd)

    r_ntc_max = calculate_ntc_resistance(temperature_list, beta + beta_percentage_tol * beta / 100.0, r_ref, temp_ref)
    r_ntc_min = calculate_ntc_resistance(temperature_list, beta - beta_percentage_tol * beta / 100.0, r_ref, temp_ref)

    v_ntc = [
        calculate_res_div(r_ntc_min, best_r1 * (1 - r1_percentage_tol / 100.0), vdd),
        calculate_res_div(r_ntc_min, best_r1 * (1 + r1_percentage_tol / 100.0), vdd),
        calculate_res_div(r_ntc_max, best_r1 * (1 - r1_percentage_tol / 100.0), vdd),
        calculate_res_div(r_ntc_max, best_r1 * (1 + r1_percentage_tol / 100.0), vdd),
    ]

    worst_case_error = []
    for i in range(len(temperature_list)):
        v_ideal = v_ntc_ideal[i]
        v_min = min(math.ceil(v / adc_lsb_voltage) * adc_lsb_voltage for v in [v_ntc[0][i], v_ntc[1][i], v_ntc[2][i], v_ntc[3][i]])
        v_max = max(math.floor(v / adc_lsb_voltage) * adc_lsb_voltage for v in [v_ntc[0][i], v_ntc[1][i], v_ntc[2][i], v_ntc[3][i]])
        error_min = abs(v_ideal - v_min)
        error_max = abs(v_ideal - v_max)
        worst_case_error.append(max(error_min, error_max))

    return worst_case_error


def select_analysis_menu():
    print("\nSelect analysis type:")
    print("1) Derivative-based selection")
    print("2) Worst-case voltage error analysis")
    print("3) Exit")
    return prompt_value('Enter choice', int, 1)


def configure_parameters():
    print("\nNTC selection helper — enter values or press Enter to accept defaults")
    return {
        'r_ref': prompt_value('Reference resistance R_ref (Ohms)', float, 10000.0),
        'temp_ref': prompt_value('Reference temperature (°C)', float, 25.0),
        'beta': prompt_value('Beta coefficient', float, 4000.0),
        'temp_target': prompt_value('Target temperature (°C) to evaluate derivative', float, 40.0),
        'vdd': prompt_value('Supply voltage for divider (V)', float, 5.0),
        'adc_lsb_voltage': prompt_value('ADC bit error voltage (mV)', float, 0.1) / 1000.0,
        'r1_percentage_tol': prompt_value('R1 tolerance (%)', float, 0.1),
        'beta_percentage_tol': prompt_value('Beta tolerance (%)', float, 0.1),
    }


def main(argv=None):
    all_e12_resistors = generate_full_e12_series()
    temperature_list = [x / 10.0 for x in range(-100, 700)]

    # Ensure Ctrl+C exits the application gracefully
    def handle_sigint(sig, frame):
        print('\nInterrupted by user. Exiting.')
        plt.close('all')
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    while True:
        choice = select_analysis_menu()
        if choice == 3:
            print('Goodbye!')
            break

        params = configure_parameters()
        temp_target = params['temp_target']
        if temp_target not in temperature_list:
            print(f"Target temperature {temp_target} not in supported range (-10.0..69.9).", file=sys.stderr)
            continue

        if choice == 1:
            run_derivative_analysis(
                params['r_ref'], params['temp_ref'], params['beta'], params['vdd'],
                temperature_list, all_e12_resistors, temperature_list.index(temp_target), temp_target
            )
        elif choice == 2:
            calculate_max_temperature_error_from_tolerances(
                params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                params['vdd'], temperature_list, params['adc_lsb_voltage'], params['r1_percentage_tol'],
                r1=10000  # Placeholder for best R1; in practice, you would determine this from derivative analysis first
            )
            plt.show()

            continue
            run_worst_case_analysis(
                params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                params['vdd'], temperature_list, all_e12_resistors, temp_target,
                params['adc_lsb_voltage'], params['r1_percentage_tol']
            )
        elif choice == 4:
            dataset = []
            for r1 in all_e12_resistors:
                all_error_list = calculate_max_temperature_error_from_tolerances(
                    params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                    params['vdd'], temperature_list, params['adc_lsb_voltage'], params['r1_percentage_tol'],
                    r1  # Placeholder for best R1; in practice, you would determine this from derivative analysis first
                )
                max_error_list = calculate_single_list_of_max_temperature_errors(all_error_list)
                dataset.append([f'R1={r1}Ω', max_error_list])
            generate_plot(
                "Temperature (°C)",
                temperature_list,
                dataset,
                 "Max temperature error vs Temperature for all R1 options"
            )
            plt.show()
        elif choice == 5:
            dataset = []
            for r1 in all_e12_resistors:
                all_error_list = calculate_max_temperature_error_from_tolerances(
                    params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                    params['vdd'], temperature_list, params['adc_lsb_voltage'], params['r1_percentage_tol'],
                    r1=r1  # Placeholder for best R1; in practice, you would determine this from derivative analysis first
                )
                max_error_list = calculate_single_list_of_max_temperature_errors(all_error_list)                
                max_error = max(max_error_list)
                dataset.append(max_error)
            generate_plot(
                "R1 (Ω)",
                all_e12_resistors,
                [["Max Temperature Error", dataset]],
                "Max temperature error vs R1"
            )
            plt.show()
        elif choice == 6:
            dataset = []
            for r1 in all_e12_resistors:
                all_error_list = calculate_max_temperature_error_from_tolerances(
                    params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                    params['vdd'], temperature_list, params['adc_lsb_voltage'], params['r1_percentage_tol'],
                    r1=r1  # Placeholder for best R1; in practice, you would determine this from derivative analysis first
                )
                max_error_list = calculate_single_list_of_max_temperature_errors(all_error_list)                
                max_error_at_target_temp = max_error_list[temperature_list.index(temp_target)]
                dataset.append(max_error_at_target_temp)
            
            min_error_idx = np.argmin(dataset)
            best_r1 = all_e12_resistors[min_error_idx]
            print(f"Best R1 option is {best_r1} Ohms (min max temperature error at {temp_target}°C = {dataset[min_error_idx]:.6g})")

            
            generate_plot(
                "R1 (Ω)",
                all_e12_resistors,
                [[f"Max Temperature Error at {temp_target}°C", dataset]],
                "Max temperature error at target temperature vs R1"
            )
            #include annotation for best R1
            fig, ax = plt.gcf(), plt.gca()
            annotate_point(ax, best_r1, dataset[min_error_idx], f'Min: {best_r1}Ω\n{dataset[min_error_idx]:.4g}')

            plt.show()
        
        elif choice == 7:
            dataset = []
            for r1 in all_e12_resistors:
                all_error_list = calculate_max_temperature_error_from_tolerances(
                    params['r_ref'], params['temp_ref'], params['beta'], params['beta_percentage_tol'],
                    params['vdd'], temperature_list, params['adc_lsb_voltage'], params['r1_percentage_tol'],
                    r1=r1  # Placeholder for best R1; in practice, you would determine this from derivative analysis first
                )
                max_error_list = calculate_single_list_of_max_temperature_errors(all_error_list)                
                dataset.append([f'R1={r1}Ω', max_error_list])
            generate_plot(
                "R1 (Ω)",
                temperature_list,
                dataset,
                "Max temperature error vs R1"
            )
            plt.show()


        else:
            print('Invalid selection, please choose 1, 2 or 3.')
            continue

        plt.show()
    plt.show()


if __name__ == '__main__':
    main()
