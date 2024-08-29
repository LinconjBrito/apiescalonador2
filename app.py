from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/fifo/submit', methods=['POST'])
def fifo():
    lista_processos = request.json[:-1]
    # lista_processos = request.json
    tempo_atual = turn_total = 0
    lista_ordenada_tempo_chegada = sorted(lista_processos, key=lambda dicionario: dicionario["T_chegada"]) #Isso ordena os processos pelo tempo de chegada
    lista_turnarounds = [0] * len(lista_ordenada_tempo_chegada)
    for k, v in enumerate(lista_ordenada_tempo_chegada): #Acessar individualmente cada dicionario(processo) dentro da lista
        if tempo_atual < v["T_chegada"]:
            tempo_atual = v["T_chegada"]
        tempo_atual += v['T_exec']
        v['Termino'] = tempo_atual
        v['Turnaround'] = v['Termino'] - v["T_chegada"]
        lista_turnarounds[k] += v['Turnaround']
        turn_total += v['Turnaround']
    turn_medio = float(turn_total / len(lista_ordenada_tempo_chegada) * 10)/10.0
    maior = max(lista_turnarounds)


    return {
        "maior": maior,
        "turnaround": turn_medio
    }
    

@app.route('/sjf/submit', methods=['POST'])
def sjf():

        lista_processos = request.json[:-1]
        tempo_atual = turn_total = i = 0
        processos_restantes = sorted(lista_processos, key=lambda dicionario: (dicionario['T_chegada'], dicionario['T_exec']))

        lista_turnarounds = [0] * len(lista_processos)
        
        contador = 0
        graficogeral = []
        for c in range(len(lista_processos)):
            graficogeral.append([])

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
            
            
            if contador == 0:
                graficogeral[processo['Id']] = [9] * tempo_atual
                espera = tempo_atual - processo['T_chegada']

                for c in range(espera):
                    graficogeral[processo['Id']].append(0)
                    
                for c in range(processo['T_exec']):
                    graficogeral[processo['Id']].append(1)

            else:
                espera = max(tempo_atual - processo['T_chegada'], 0)
                for c in range(tempo_atual - espera):
                    graficogeral[processo['Id']].append(9)
                if espera == 0:
                    graficogeral[processo['Id']] = [9] * tempo_atual
                else:
                    for c in range(tempo_atual - processo['T_chegada']):
                        graficogeral[processo['Id']].append(0)
                for c in range(processo['T_exec']):
                    graficogeral[processo['Id']].append(1)
            contador += 1


            tempo_atual += processo['T_exec']
            processo['Termino'] = tempo_atual  # Atualizado para calcular o tempo de término
            processo['Turnaround'] = processo['Termino'] - processo['T_chegada']
            lista_turnarounds[i] += processo['Turnaround']
            i += 1
            turn_total += processo['Turnaround']
        
        turn_medio = float(turn_total / len(lista_processos) * 10)/10.0
        maior = max(lista_turnarounds)
        
        maiorlista = max(graficogeral, key=len)
        for c in graficogeral:
            for k in range(len(maiorlista) - len(c)):
                c.append(9)
        

        return {
            "grafico": graficogeral,
            "maior": maior,
            "turnaround": turn_medio
        }
        

@app.route('/edf/submit', methods=['POST'])
def edf():

    lista_processos = request.json
    lista_tempo_chegada = [] 
    lista_tempo_execucao = []
    lista_deadlines = []
    lista_parametros_deadlines = []

     
    for k, v in enumerate(lista_processos):

        if 'T_chegada' in v:
            lista_tempo_chegada.append(v['T_chegada'])

        if 'T_exec' in v:
            lista_tempo_execucao.append(v['T_exec'])

        if 'Deadline' in v:
            lista_deadlines.append(v['Deadline'])
        
        if 'Deadline' in v:
            lista_parametros_deadlines.append(v['Deadline'])
        # setando os valores do sistema
        if 'quantum' in v:
            quantum = v['quantum']
        if "qtd_processos" in v:
            qtd_processos = v['qtd_processos']
        if "sobrecarga" in v:
            sobrecarga = v['sobrecarga']

    lista_de_turnarounds = [0]*qtd_processos

    global tempo_edf
    tempo_edf = int(min(lista_tempo_chegada))
    turnaround = 0
    tempo_cpu = [0]*qtd_processos  
    lista_processamento = [0]*qtd_processos 
    grafico = []
    for i in range(qtd_processos):
        linha = []
        grafico.append(linha) 

    def verificaFila():
        for x in range(0,qtd_processos):
            if lista_tempo_chegada[x] <= tempo_edf and lista_processamento[x] == 0:
                lista_processamento[x] = 1
            pass
    verificaFila()
    def firstKill():
        deadline_proxima = 1000
        global escolhido
        escolhido = -1
        for x in range(0,qtd_processos):
            if lista_processamento[x] == 1 and lista_deadlines[x] < deadline_proxima and tempo_cpu[x] < lista_tempo_execucao[x]:
                deadline_proxima = lista_deadlines[x]
                escolhido = x
            pass
        for x in range(0,qtd_processos):
            if escolhido == -1 and lista_processamento[x] == 0:
                deadline_proxima = lista_deadlines[x]
                escolhido = x
                global tempo_edf
                tempo_edf = lista_tempo_chegada[x]
            pass
        return escolhido
       
    while firstKill() != -1:
        resta_executar = lista_tempo_execucao[escolhido]-tempo_cpu[escolhido] 
        if resta_executar > quantum:
            tempo_edf+=quantum
            tempo_cpu[escolhido] += quantum
            for x in range(0,qtd_processos):
                if lista_tempo_chegada[x] <= tempo_edf and tempo_cpu[x]<lista_tempo_execucao[x]:
                    lista_deadlines[x] = lista_parametros_deadlines[x] - tempo_edf
            for p in range(qtd_processos):
                if p == escolhido:
                    for i in range(int(quantum)):
                        if lista_deadlines[p] >= 0:
                            grafico[p].append(1)
                        else:
                            grafico[p].append(8)
                else:
                    if lista_tempo_chegada[p] < tempo_edf and tempo_cpu[p]!=lista_tempo_execucao[p]:
                        if (tempo_edf - lista_tempo_chegada[p]) == tempo_edf and grafico[p] == []:
                            for i in range(int(quantum)):
                                grafico[p].append(0)
                        elif (tempo_edf - lista_tempo_chegada[p]) < tempo_edf and grafico[p] == []:
                            for i in range(int(lista_tempo_chegada[p])):
                                grafico[p].append(9)
                            for i in range(int(quantum-lista_tempo_chegada[p])):
                                grafico[p].append(0)
                        else:
                            for i in range(int(quantum)):
                                grafico[p].append(0)
                    elif lista_tempo_chegada[p]<= tempo_edf and tempo_cpu[p]==lista_tempo_execucao[p]:
                        for i in range(int(quantum)):
                            grafico[p].append(9)
                    elif lista_tempo_chegada[p] > tempo_edf:
                        for i in range(int(quantum)):
                            grafico[p].append(9)
                    elif lista_tempo_chegada[p] == tempo_edf and tempo_cpu[p]!=lista_tempo_execucao[p]:
                        for i in range(int(quantum)):
                            grafico[p].append(9)   
            verificaFila() 
            tempo_edf+=sobrecarga
            for x in range(0,qtd_processos): 
                if lista_tempo_chegada[x] <= tempo_edf and tempo_cpu[x]<lista_tempo_execucao[x]: 
                    lista_deadlines[x] = lista_parametros_deadlines[x] - tempo_edf 
            for p in range(qtd_processos):
                if p == escolhido:
                    for i in range(int(sobrecarga)):
                        grafico[p].append(3)
                else:
                    if lista_tempo_chegada[p]< tempo_edf and tempo_cpu[p]!=lista_tempo_execucao[p]:
                        for i in range(int(sobrecarga)):
                            grafico[p].append(0)
                    elif lista_tempo_chegada[p]<= tempo_edf and tempo_cpu[p]==lista_tempo_execucao[p]:
                        for i in range(int(sobrecarga)):
                            grafico[p].append(9)
                    elif lista_tempo_chegada[p] > tempo_edf:
                        for i in range(int(sobrecarga)):
                            grafico[p].append(9)
            verificaFila()
        elif resta_executar <= quantum and resta_executar > 0: 
            tempo_edf+= resta_executar
            for x in range(0,qtd_processos): 
                if lista_tempo_chegada[x] <= tempo_edf and tempo_cpu[x]<lista_tempo_execucao[x]:
                    lista_deadlines[x] = lista_parametros_deadlines[x] - tempo_edf
            for p in range(qtd_processos):
                if p == escolhido:
                    if lista_deadlines[p] >= 0:
                        for i in range(int(resta_executar)):
                            grafico[p].append(1)
                    else:
                        for i in range(int(resta_executar)):
                            grafico[p].append(8)
                else:
                    if lista_tempo_chegada[p]< tempo_edf and tempo_cpu[p]!=lista_tempo_execucao[p]:
                        for i in range(int(resta_executar)):
                            grafico[p].append(0)
                    elif lista_tempo_chegada[p]<= tempo_edf and tempo_cpu[p]==lista_tempo_execucao[p]:
                        for i in range(int(resta_executar)):
                            grafico[p].append(9)
                    elif lista_tempo_chegada[p] > tempo_edf:
                        for i in range(int(resta_executar)):
                            grafico[p].append(9)
                    elif lista_tempo_chegada[p] == tempo_edf and tempo_cpu[p]!=lista_tempo_execucao[p]:
                        for i in range(int(resta_executar)):
                            grafico[p].append(9)  
            lista_de_turnarounds[escolhido]+=tempo_edf-lista_tempo_chegada[escolhido]
            verificaFila() 
            tempo_cpu[escolhido]+=quantum 
            turnaround+=tempo_edf-lista_tempo_chegada[escolhido] 

    turn_medio = float(turnaround/qtd_processos)
    turn_medio = float(turnaround/qtd_processos * 10) / 10.0
    maior = max(lista_de_turnarounds) 
    return {
        "grafico": grafico,
        "maior": maior,
        "turnaround": turn_medio
    }



@app.route('/rr/submit', methods=['POST'])
def rr():
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

    lista_de_turnarounds = [0]*qtd_processos

    global tempo_rr
    tempo_rr = int(min(lista_tempo_chegada))
    turnaround = 0
    tempo_cpu = [0]*qtd_processos  
    lista_processamento = [0]*qtd_processos  
    lista_circular = [] 
    grafico = []
    for i in range(qtd_processos):
        linha = []
        grafico.append(linha)

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
            tempo_cpu[p]+=quantum
            for x in range(qtd_processos):
                if x == p:
                    for i in range(int(quantum)):
                        grafico[x].append(1)
                else:
                    if lista_tempo_chegada[x] < tempo_rr and tempo_cpu[x]!=lista_tempo_execucao[x]:
                        if (tempo_rr - lista_tempo_chegada[x]) == tempo_rr and grafico[x] == []:
                            for i in range(int(quantum)):
                                grafico[x].append(0)
                        elif (tempo_rr - lista_tempo_chegada[x]) < tempo_rr and grafico[x] == []:
                            for i in range(int(lista_tempo_chegada[x])):
                                grafico[x].append(9)
                            for i in range(int(quantum-lista_tempo_chegada[x])):
                                grafico[x].append(0)
                        else:
                            for i in range(int(quantum)):
                                grafico[x].append(0)   
                    elif lista_tempo_chegada[x]<= tempo_rr and tempo_cpu[x]==lista_tempo_execucao[x]:
                        for i in range(int(quantum)):
                            grafico[x].append(9)
                    elif lista_tempo_chegada[x] > tempo_rr:
                        for i in range(int(quantum)):
                            grafico[x].append(9)
                    elif lista_tempo_chegada[x] == tempo_rr and tempo_cpu[x]!=lista_tempo_execucao[x]:
                        for i in range(int(quantum)):
                            grafico[x].append(9)
            verificaFila()
            tempo_rr+= sobrecarga
            for x in range(qtd_processos):
                if x == p:
                    for i in range(int(sobrecarga)):
                        grafico[p].append(3)
                else:
                    if lista_tempo_chegada[x] < tempo_rr and tempo_cpu[x]!=lista_tempo_execucao[x]:
                        for i in range(int(sobrecarga)):
                            grafico[x].append(0)
                    elif lista_tempo_chegada[x] <= tempo_rr and tempo_cpu[x]==lista_tempo_execucao[x]:
                        for i in range(int(sobrecarga)):
                            grafico[x].append(9)
                    elif lista_tempo_chegada[x] > tempo_rr:
                        for i in range(int(sobrecarga)):
                            grafico[x].append(9)
            verificaFila()
            lista_circular.remove(p)
            lista_circular.append(p)
        elif resta_executar <= quantum and resta_executar > 0 :
            tempo_rr+=resta_executar
            lista_de_turnarounds[p]+=tempo_rr-lista_tempo_chegada[p]
            verificaFila()
            tempo_cpu[p]+=resta_executar
            for x in range(qtd_processos):
                if x == p:
                    for i in range(int(resta_executar)):
                        grafico[p].append(1)
                elif x != p:
                    if lista_tempo_chegada[x]< tempo_rr and tempo_cpu[x]!=lista_tempo_execucao[x]:
                        for i in range(int(resta_executar)):
                            grafico[x].append(0)
                    elif lista_tempo_chegada[x]<= tempo_rr and tempo_cpu[x]==lista_tempo_execucao[x]:
                        for i in range(int(resta_executar)):
                            grafico[x].append(9)
                    elif lista_tempo_chegada[x] > tempo_rr:
                        for i in range(int(resta_executar)):
                            grafico[x].append(9)
                    elif lista_tempo_chegada[x] == tempo_rr and tempo_cpu[x]!=lista_tempo_execucao[x]:
                        for i in range(int(resta_executar)):
                            grafico[x].append(9)    
            turnaround+=tempo_rr-lista_tempo_chegada[p]
            lista_circular.remove(p)
            verificaFila()

    maior = max(lista_de_turnarounds)
    turn_medio = float(turnaround/qtd_processos * 10) / 10.0

    return {
        "grafico": grafico,
        "maior": maior,
        "turnaround": turn_medio
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
