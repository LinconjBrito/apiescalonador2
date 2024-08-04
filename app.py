from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/fifo/submit', methods=['POST'])
def calc_turnaround_fifo():
    lista_processos = request.json
    tempo_atual = turn_total = 0
    lista_ordenada_tempo_chegada = sorted(lista_processos, key=lambda dicionario: dicionario['T_chegada']) #Isso ordena os processos pelo tempo de chegada
    for k, v in enumerate(lista_ordenada_tempo_chegada): #Acessar individualmente cada dicionario(processo) dentro da lista
        if tempo_atual < v['T_chegada']:
                tempo_atual = v['T_chegada']
        tempo_atual += v['T_exec']
        v['Termino'] = tempo_atual
        v['Turnaround'] = v['Termino'] - v['T_chegada']
        turn_total += v['Turnaround']
    turn_medio = turn_total / len(lista_ordenada_tempo_chegada)


    response = {
         "turnaround" : turn_medio
    }
    return jsonify(response)


@app.route('/sjf/submit', methods=['POST'])
def calc_turnaround_sjf():
        lista_processos = request.json
        tempo_atual = turn_total = 0
        processos_restantes = sorted(lista_processos, key=lambda dicionario: (dicionario['T_chegada'], dicionario['T_exec']))
        
        while processos_restantes:
            processos_disponiveis = []
            for k, v in enumerate(processos_restantes):
                if v['T_chegada'] <= tempo_atual:
                    processos_disponiveis.append(v)

            
            if not processos_disponiveis:
                tempo_atual = processos_restantes[0]['T_chegada']
                processos_disponiveis = []
                for k, v in enumerate(processos_restantes):
                    if v['T_chegada'] <= tempo_atual:
                        processos_disponiveis.append(v)

            processo = min(processos_disponiveis, key=lambda dicionario: dicionario['T_exec'])
            processos_restantes.remove(processo)
            
            tempo_atual += processo['T_exec']
            processo['Termino'] = tempo_atual  # Atualizado para calcular o tempo de término
            processo['Turnaround'] = processo['Termino'] - processo['T_chegada']
            turn_total += processo['Turnaround']
        
        turn_medio = turn_total / len(lista_processos)
        response = {
             "turnaround" : turn_medio
        }
        return jsonify(response) 

@app.route('/edf/submit', methods=['POST'])
def edf():

    lista_processos = request.json
    lista_tempo_chegada = [] 
    lista_tempo_execucao = []
    lista_deadlines = []
     
    for k, v in enumerate(lista_processos):


        if 'T_chegada' in v:
            lista_tempo_chegada.append(v['T_chegada'])

        if 'T_exec' in v:
            lista_tempo_execucao.append(v['T_exec'])

        if 'Deadline' in v:
            lista_deadlines.append(v['Deadline'])

        # setando os valores do sistema
        if 'quantum' in v:
            quantum = v['quantum']
        if "qtd_processos" in v:
            qtd_processos = v['qtd_processos']
        if "sobrecarga" in v:
            sobrecarga = v['sobrecarga']

    global tempo_edf
    tempo_edf = int(min(lista_tempo_chegada))
    turnaround = 0
    tempo_cpu = [0]*qtd_processos  
    lista_processamento = [0]*qtd_processos  

    def verificaFila():
        for x in range(0,qtd_processos):
            if lista_tempo_chegada[x] <= tempo_edf and lista_processamento[x] == 0:
                lista_processamento[x] = 1
            pass
    verificaFila()
    def firstKill():
        deadline_proxima = 1000
        escolhido = -1
        for x in range(0,qtd_processos):
            if lista_processamento[x] == 1 and lista_deadlines[x] < deadline_proxima and tempo_cpu[x] < lista_tempo_execucao[x]:
                deadline_proxima = lista_deadlines[x]
                escolhido = x
        for x in range(0,qtd_processos):
            if escolhido == -1 and lista_processamento[x] == 0:
                deadline_proxima = lista_deadlines[x]
                escolhido = x
                global tempo_edf
                tempo_edf = lista_tempo_chegada[x]
        return escolhido

    verificaFila()        
    while firstKill() != -1:
        p = firstKill()
        resta_executar = lista_tempo_execucao[p]-tempo_cpu[p] 
        if resta_executar > quantum:
            tempo_edf+=quantum
            lista_deadlines[p] -= quantum
            verificaFila()
            tempo_cpu[p]+=quantum 
            tempo_edf+=sobrecarga
            lista_deadlines[p] -= quantum
            verificaFila()
        elif resta_executar == quantum and resta_executar > 0: 
            tempo_edf+=quantum
            lista_deadlines[p] -= quantum
            verificaFila() 
            tempo_cpu[p]+=quantum 
            turnaround+=tempo_edf-lista_tempo_chegada[p] 
        elif resta_executar < quantum:
            tempo_edf+= resta_executar
            lista_deadlines[p] -= quantum
            verificaFila()
            tempo_cpu[p]+=resta_executar
            turnaround+=tempo_edf-lista_tempo_chegada[p]

    turn_medio = float(turnaround/qtd_processos)
    response = {
        "turnaround" : turn_medio
    }
    return response

@app.route('/rr/submit', methods=['POST'])
def round_r():
    lista_processos = request.json
    
    lista_tempo_chegada = [] 
    lista_tempo_execucao = []


    for k, v in enumerate(lista_processos):

        if 'T_chegada' in v:
            lista_tempo_chegada.append(v['T_chegada'])

        if 'T_exec' in v:
            lista_tempo_execucao.append(v['T_exec'])

        # setando os valores do sistema
        if 'quantum' in v:
            quantum = v['quantum']
        if "qtd_processos" in v:
            qtd_processos = v['qtd_processos']
        if "sobrecarga" in v:
            sobrecarga = v['sobrecarga']

    global tempo_rr
    tempo_rr = int(min(lista_tempo_chegada))
    turnaround = 0
    tempo_cpu = [0]*qtd_processos  
    lista_processamento = [0]*qtd_processos  
    lista_circular = [] 

    def verificaFila():
        global tempo_rr
        for x in range(0,qtd_processos):
            if lista_tempo_chegada[x] <= tempo_rr and lista_processamento[x] == 0:
                lista_processamento[x] = 1 
                lista_circular.append(x)
        for x in range(0,qtd_processos):
            if lista_tempo_chegada[x] > tempo_rr and lista_processamento[x] == 0 and lista_circular == []:
                lista_processamento[x] = 1
                tempo_rr = lista_tempo_chegada[x]
                lista_circular.append(x)
            pass
    verificaFila()

    while lista_circular != []:
        p = lista_circular[0]
        resta_executar = lista_tempo_execucao[p]-tempo_cpu[p]  
        if resta_executar > quantum:
            tempo_rr+= quantum
            verificaFila()
            tempo_cpu[p]+=quantum
            tempo_rr+= sobrecarga
            verificaFila()
            lista_circular.remove(p)
            lista_circular.append(p)
        elif resta_executar == quantum and resta_executar > 0 :
            tempo_rr+=quantum
            verificaFila()
            tempo_cpu[p]+=quantum
            turnaround+=tempo_rr-lista_tempo_chegada[p]
            lista_circular.remove(p)
            verificaFila()
        elif resta_executar < quantum:
            tempo_rr+= resta_executar
            verificaFila()
            tempo_cpu[p]+=resta_executar
            turnaround+=tempo_rr-lista_tempo_chegada[p]
            lista_circular.remove(p)
            verificaFila()
    
    turn_medio = float(turnaround/qtd_processos)
    response = {
        "turnaround" : turn_medio
    }
    return response 




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)




#meu_dicionario = [{'T_chegada': 11, 'T_exec': 3, 'Termino': 0, 'Turnaround': 0}, {'T_chegada': 4, 'T_exec': 4, 'Termino': 0, 'Turnaround': 0}, {'T_chegada': 2, 'T_exec': 1, 'Termino': 0, 'Turnaround': 0}, {'T_chegada': 2, 'T_exec': 3, 'Termino': 0, 'Turnaround': 0}] # Caso de teste




# [{"T_chegada": 11, "T_exec": 3, "Termino": 0, "Turnaround": 0}, {"T_chegada": 4, "T_exec": 4, "Termino": 0, "Turnaround": 0}, {"T_chegada": 2, "T_exec": 1, "Termino": 0, "Turnaround": 0}, {"T_chegada": 2, "T_exec": 3, "Termino": 0, "Turnaround": 0}] # Caso de teste no postman