from .juggling_dlx_milp import *
import ipywidgets

def solve_and_print(music, nb_hands, max_height, max_weight, forbidden_multiplex, method="DLX", optimize=True, maximize=[]):
    balls, throws = music_to_throws(music)
    ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                 forbidden_multiplex, True)
    sol = None
    if method == "DLX":
        sol = get_solution_with_dlx(ec_instance, maximize)
    elif method == "MILP":
        sol = solve_exact_cover_with_milp(ec_instance, optimize, maximize)
    if len(sol) == 0:
        raise RuntimeError("No solution.")
    jsol = exact_cover_solution_to_juggling_solution(sol)

    print_juggling(jsol)
    return jsol


def solve_and_simulate(music, nb_hands, max_height, max_weight, forbidden_multiplex, colors, sides, method="DLX", optimize=True, maximize=[], step=10):
    balls, throws = music_to_throws(music)
    ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                 forbidden_multiplex, True)
    sol = None
    if method == "DLX":
        sol = get_solution_with_dlx(ec_instance, maximize)
    elif method == "MILP":
        sol = solve_exact_cover_with_milp(ec_instance, optimize, maximize)
    if len(sol) == 0:
        raise RuntimeError("No solution.")
    jsol = exact_cover_solution_to_juggling_solution(sol)
    balls, pattern = juggling_sol_to_simulator(jsol, colors)

    model = modele.Model(balls, pattern)
    # slider = ipywidgets.FloatSlider(min=0, max=40, step=0.05)
    play = ipywidgets.Play(
        value=0,
        min=0,
        max=4000,
        step=step,
        interval=30,
        description="Press play",
        disabled=False
    )
    slider = ipywidgets.IntSlider(min=0, max=4000)
    ipywidgets.jslink((play, 'value'), (slider, 'value'))
    view = modele.View(model, sides)
    slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")
    return ipywidgets.VBox([view.widget, ipywidgets.HBox([play, slider])])

# ============================================================================ #
#                                                                              #
#     FONCTIONS DE D'AFFICHAGE EN TEXTE DE LA SÉQUENCE DE JONGLAGE OBTENUE     #
#                    EN RESULTAT DE L'ALGORITHME                               #
#                                                                              #
# ============================================================================ #


def print_juggling_solution(sol):
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                print("{} - {} : main {} ({} temps) --> {} temps"
                      .format(str(item.throw.time), item.throw.ball, item.hand,
                              item.throw.max_height - item.flying_time,
                              item.flying_time))


def juggling_to_formatted_str(sol: JugglingSolution):
    max_time = sol.params['max_time']
    in_hand: List[List[Set[str]]] = [[set() for _ in range(sol.params['nb_hands'])]
                                     for _ in range(max_time + 1)]
    hand: List[Dict[str, int]] = [{} for _ in range(max_time + 1)]
    throws: List[List[Tuple[str, int]]] = [[] for _ in range(max_time + 1)]
    last_throws: List[FinalThrow] = []

    for throw in sol.throws:
        for t in range(throw.time_in_hand + 1):
            in_hand[throw.time + t][throw.src_hand].add(throw.ball)
            hand[throw.time + t][throw.ball] = throw.src_hand
        for throw1 in last_throws:
            if throw.ball == throw1.ball and throw.time > throw1.time:
                last_throws.remove(throw1)
                last_throws.append(throw)
                break
        else:
            for throw1 in last_throws:
                if throw.ball == throw1.ball:
                    break
            else:
                last_throws.append(throw)
        throws[throw.time + throw.time_in_hand] \
            .append((throw.ball, throw.flying_time))
    for throw in last_throws:
        for t in range(throw.time + throw.full_time, max_time + 1):
            hand[t][throw.ball] = throw.dst_hand
            in_hand[t][throw.dst_hand].add(throw.ball)
    max_hand_width = [0 for i in range(sol.params['nb_hands'])]
    for t in range(max_time):
        for i in range(sol.params['nb_hands']):
            h = in_hand[t][i]
            s = (str(h) if len(h) > 0 else "{}") + " "
            if len(s) > max_hand_width[i]:
                max_hand_width[i] = len(s)
    max_hands_width = sum(max_hand_width)
    output = ""
    for t in range(max_time):
        s = ""
        for i in range(sol.params['nb_hands']):
            h = in_hand[t][i]
            s1 = (str(h) if len(h) > 0 else "{}") + " "
            s += ("{:^" + str(max_hand_width[i]) + "}").format(s1)
        s += ": "
        if len(throws[t]) > 0:
            ball, flying_time = throws[t][0]
            s += "{} -- {} --> {}" \
                 .format(ball, flying_time,
                         hand[t + flying_time][ball]
                         if ball in hand[t + flying_time] else "?")
            output += s + "\n"
            for i in range(1, len(throws[t])):
                ball, flying_time = throws[t][i]
                output += " " * (max_hands_width + 2)
                output += "{} -- {} --> {}" \
                    .format(ball, flying_time,
                            hand[t + flying_time][ball]
                            if ball in hand[t + flying_time] else "?") + "\n"
        else:
            output += s + "\n"
    return output


def print_juggling(sol: JugglingSolution):
    print(juggling_to_formatted_str(sol))
    return None


def display_interface():
    out = ipywidgets.Output()

    l_inttext = ipywidgets.Layout(width='100px')
    l_text = ipywidgets.Layout(width='150px')
    l_simulation_text = ipywidgets.Layout(width='400px')

    w_nb_hands = ipywidgets.IntText(
        value=2,
        disabled=False,
        layout=l_inttext
    )
    w_max_weight = ipywidgets.IntText(
        value=3,
        disabled=False,
        layout=l_inttext
    )
    w_max_height = ipywidgets.IntText(
        value=5,
        disabled=False,
        layout=l_inttext
    )
    w_no_multiplex = ipywidgets.Checkbox(
        value=False,
        disabled=False,
        indent=False
    )
    w_generate_forbidden_multiplex = ipywidgets.Button(
        description='Générer',
        disabled=False,
        button_style='',
        icon='refresh'
    )
    w_forbidden_multiplex = ipywidgets.SelectMultiple(
        options=[''],
        value=[],
        disabled=False,
    )
    w_forbidden_throws = ipywidgets.Text(
        value='',
        placeholder='',
        disabled=False
    )

    def fill_forbidden_multiplex(args):
        nonlocal w_forbidden_multiplex
        old_options = w_forbidden_multiplex.options
        selected = w_forbidden_multiplex.value
        max_height = w_max_height.value
        options = []
        for i in range(1, max_height + 1):
            for j in range(i, max_height + 1):
                options.append(str(i) + ", " + str(j))
        w_forbidden_multiplex.options = options
        w_forbidden_multiplex.disabled = w_no_multiplex.value
        new_selected = []
        for s in selected:
            i = int(s.split(', ')[0])
            j = int(s.split(', ')[1])
            if i <= max_height and j <= max_height:
                new_selected.append(str(i) + ', ' + str(j))
        w_forbidden_multiplex.value = new_selected
        # logger.debug(old_options)
        if len(old_options) == 1:
            w_forbidden_multiplex.selected = ["1, 1", "1, 2", "1, 3", "1, 4", "1, 5"]
        out.clear_output()
        with out:
            display(ui)

    w_maximize = ipywidgets.Text(
        value='',
        placeholder='',
        disabled=False
    )
    w_generate_hands = ipywidgets.Button(
        description='Générer',
        disabled=False,
        button_style='',
        icon='refresh'
    )
    hands_constraints = {}
    w_hands_constraints = ipywidgets.Accordion([])

    def fill_hand_constraints(args):
        nonlocal hands_constraints, w_hands_constraints
        max_weight_old = len(hands_constraints) + 1
        max_weight = w_max_weight.value
        if max_weight > max_weight_old:
            for k in range(max_weight_old + 1, max_weight + 1):
                w_throw = ipywidgets.BoundedIntText(value=1, min=1, max=k, step=1, disabled=False, layout=l_text)
                w_catch = ipywidgets.BoundedIntText(value=k, min=1, max=k, step=1, disabled=False, layout=l_text)
                w_perm = ipywidgets.Text(value='', placeholder='', disabled=False, layout=l_text)
                hands_constraints[k] = {
                    'throw': w_throw,
                    'catch': w_catch,
                    'perm': w_perm,
                    'box': ipywidgets.GridBox([
                        ipywidgets.Label('Lancer :'), w_throw,
                        ipywidgets.Label('Récupération :'), w_catch,
                        ipywidgets.Label('Permutations :'), w_perm
                    ], layout=ipywidgets.Layout(grid_template_columns="repeat(2, 100px)"))
                }
        else:
            for k in range(max_weight + 1, max_weight_old + 1):
                hands_constraints.pop(k)
        w_hands_constraints = ipywidgets.Accordion([hands_constraints[k]['box'] for k in range(2, max_weight + 1)], layout=ipywidgets.Layout(width='300px'))
        for k in range(2, max_weight + 1):
            w_hands_constraints.set_title(index=k - 2, title=str(k) + " mains")
        tab.children = [tab1, tab2, tab3()]
        out.clear_output()
        with out:
            display(ui)

    def tab3():
        return ipywidgets.GridBox([
            ipywidgets.Label('Contraintes sur les mains :'), w_generate_hands,
            ipywidgets.Label(''), w_hands_constraints
        ], layout=ipywidgets.Layout(grid_template_columns="repeat(2, 210px)"))
    tab1 = ipywidgets.GridBox([
        ipywidgets.Label('Nombre de mains :'), w_nb_hands,
        ipywidgets.Label('Nombre maximal de balles dans une main :'), w_max_weight,
        ipywidgets.Label('Hauteur maximale :'), w_max_height
    ], layout=ipywidgets.Layout(grid_template_columns="repeat(2, 260px)"))
    tab2 = ipywidgets.GridBox([
        ipywidgets.Label('Maximiser les lancers :'), w_maximize,
        ipywidgets.Label('Aucun lancer multiple :'), w_no_multiplex,
        ipywidgets.Label('Lancers interdits :'), w_forbidden_throws,
        ipywidgets.Label('Lancers multiples interdits :'), w_generate_forbidden_multiplex,
        ipywidgets.VBox([
            ipywidgets.Label('(maintenir Ctrl pour', layout=ipywidgets.Layout(height='20px')),
            ipywidgets.Label('sélectionner/désélectionner)', layout=ipywidgets.Layout(height='20px'))]),
        w_forbidden_multiplex
    ], layout=ipywidgets.Layout(grid_template_columns="repeat(2, 170px)"))

    tab = ipywidgets.Tab(layout=ipywidgets.Layout(width='550px', margin='0px 0px 10px 0px'))
    tab.children = [tab1, tab2, tab3()]
    tab.set_title(index=0, title="Général")
    tab.set_title(index=1, title="Lancers")
    tab.set_title(index=2, title="Mains")

    model = modele.Model({}, [[], []])
    play = ipywidgets.Play(
        value=0,
        min=0,
        max=4000,
        step=5,
        interval=30,
        description="Press play",
        disabled=False
    )
    slider = ipywidgets.IntSlider(min=0, max=4000)
    ipywidgets.jslink((play, 'value'), (slider, 'value'))
    view = modele.View(model, [-1, -1, 1])
    slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")

    w_music = ipywidgets.Textarea(
        value='[1 C4] [2 C4] [3 C4] [4 D4] [5 E4] [7 D4] [9 C4] [10 E4] [11 D4] [12 D4] [13 C4]',
        placeholder='',
        description='',
        disabled=False,
        layout=ipywidgets.Layout(width='475px', margin='0px 0px 10px 0px')
    )
    w_working = ipywidgets.Label('Prêt')
    w_solve = ipywidgets.Button(
        description='Résoudre les contraintes',
        disabled=False,
        button_style='',
        icon='check',
        layout=ipywidgets.Layout(width='345px')
    )
    w_simulate = ipywidgets.Button(
        description='Simuler',
        disabled=True,
        button_style='',
        icon='check',
        layout=ipywidgets.Layout(width='200px')
    )
    w_step = ipywidgets.IntText(
        value=5,
        disabled=False,
        layout=l_inttext
    )
    w_sides = ipywidgets.Text(
        value='-1, 1',
        placeholder='',
        disabled=False,
        layout=l_simulation_text
    )
    w_colors = ipywidgets.Text(
        value='blue, red, green, yellow, purple, cyan, magenta',
        placeholder='',
        disabled=False,
        layout=l_simulation_text
    )
    w_method = ipywidgets.RadioButtons(
        options=['Programmation Linéaire (rapide, ne respecte pas les contraintes sur les mains)',
                 'Dancing Links (lent, respecte les contraintes sur les mains)'],
        description='',
        disabled=False,
        layout={'width': 'max-content'}
    )
    w_result = ipywidgets.Textarea(
        value='',
        placeholder='',
        disabled=True,
        layout={'width': '516px', 'height': '553px'}
    )

    # balls = {}
    # pattern = [[], []]
    jsol = None
    tab_res_sim = ipywidgets.Tab()

    def ui_view(view, play, slider):
        tab_res_sim.children = [ipywidgets.VBox([view.widget, ipywidgets.HBox([play, slider])], layout=ipywidgets.Layout(margin="10px")), w_result]
        tab_res_sim.set_title(index=0, title="Simulation")
        tab_res_sim.set_title(index=1, title="Résultat")
        return ipywidgets.HBox([
            ipywidgets.VBox([
                ipywidgets.HBox([ipywidgets.Label('Musique :', layout=ipywidgets.Layout(width='70px')), w_music]),
                tab,
                ipywidgets.GridBox([
                    ipywidgets.Label('Pas :'), w_step,
                    ipywidgets.Label('Orientation des mains :'), w_sides,
                    ipywidgets.Label('Couleurs :'), w_colors
                ], layout=ipywidgets.Layout(grid_template_columns='repeat(2, 150px)')),
                w_working,
                w_method,
                ipywidgets.HBox([w_solve, w_simulate])], layout=ipywidgets.Layout(margin="10px")),
            tab_res_sim
        ])

    def solve(args):
        nonlocal jsol
        if w_working.value != "Prêt":
            return
        music = []
        for s in w_music.value.split('] ['):
            s1 = s.strip()
            if s1[0] == '[':
                s1 = s1[1:]
            elif s1[-1] == ']':
                s1 = s1[:-1]
            p = s1.split(' ')
            for i in range(1, len(p)):
                music.append((int(p[0]), p[i]))

        nb_hands = w_nb_hands.value
        max_height = w_max_height.value
        max_weight = w_max_weight.value
        forbidden_multiplex = []
        if w_forbidden_throws.value.strip() != '':
            for s in w_forbidden_throws.value.split(' '):
                i = int(s)
                forbidden_multiplex.append((i, ))
        for s in w_forbidden_multiplex.value:
            i = int(s.split(', ')[0])
            j = int(s.split(', ')[1])
            forbidden_multiplex.append((i, j))
        maximize = [int(s) for s in w_maximize.value.split(' ')] if w_maximize.value.strip() != '' else []
        method = 'DLX' if w_method.value.startswith('Dancing Links') else 'MILP'
        optimize = w_maximize.value != ""
        w_working.value = "En cours..."
        balls, throws = music_to_throws(music)
        ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                     forbidden_multiplex, True)
        sol = None
        if method == "DLX":
            sol = get_solution_with_dlx(ec_instance, maximize=maximize)
        elif method == "MILP":
            sol = solve_exact_cover_with_milp(ec_instance, optimize=optimize, maximize=maximize)
        if len(sol) == 0:
            raise RuntimeError("No solution.")
        jsol = exact_cover_solution_to_juggling_solution(sol)
        formatted_str = juggling_to_formatted_str(jsol)
        w_result.value = formatted_str
        w_working.value = "Prêt"
        w_simulate.disabled = False
        tab_res_sim.selected_index = 1

    def simulate(args):
        colors = w_colors.value.split(', ')
        sides = [int(x) for x in w_sides.value.split(', ')]
        step = w_step.value
        balls, pattern = juggling_sol_to_simulator(jsol, colors)
        model = modele.Model(balls, pattern)
        play = ipywidgets.Play(
            value=0,
            min=0,
            max=4000,
            step=step,
            interval=30,
            description="Press play",
            disabled=False
        )
        slider = ipywidgets.IntSlider(min=0, max=4000)
        ipywidgets.jslink((play, 'value'), (slider, 'value'))
        view = modele.View(model, sides, out)
        slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")
        with out:
            out.clear_output()
            tab_res_sim.selected_index = 0
            display(ui_view(view, play, slider))

    w_generate_forbidden_multiplex.on_click(fill_forbidden_multiplex)
    w_generate_hands.on_click(fill_hand_constraints)
    w_solve.on_click(solve)
    w_simulate.on_click(simulate)

    ui = ui_view(view, play, slider)

    with out:
        display(ui)
    return out