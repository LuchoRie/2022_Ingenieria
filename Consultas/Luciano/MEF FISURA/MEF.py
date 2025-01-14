import numpy as np

def solve(K, r, s, Us, Fr):
    """
    #
    Se deben ingresar:
    K = matriz global de constantes elásticas
    r = posicion de los desplazamientos desconocidos (fuerzas conocidas)
    s = posición de los desplazamientos conocidos 
    Us = valor de los desplazamientos conocidos [vector columnar]
    Fr = valor de las fuerzas conocidas [vector columnar]
    
    mef.solve devuelve 2 vectores, uno con las fuerzas en cada nodo (F) y otro con los desplazamientos respectivamente (U)
    #
    """
    N = np.shape(K)[1]  # Nro. de nodos * glxn
    F = np.zeros([N,1])
    U = np.zeros([N,1])
    U[s] = Us
    F[r] = Fr
    Kred = K[np.ix_(r,r)]
    Kvin = K[np.ix_(r,s)]
    
    # Los 'r' son los desplazamientos incognitos, los 's' son los desplazamientos que tenemos como dato
    
    U[r] = np.linalg.solve(Kred, F[r]-Kvin.dot(U[s]))
    F[s] = K[s,:].dot(U)
    
    return F, U

def tensiones(MC, U, D, B, glxn):
    sig = {}
    d = {}
    Ne = MC.shape[0]
    for e in range(Ne):
        nodo = MC[e,:].astype(int)  # nodos del elemento [e] analizado en cada ciclo
        d[e] = np.array([U[nodo[0]*glxn],U[nodo[0]*glxn+1],  # d = obtiene la tensión en cada elemento en función de los despl de cada elemento
                         U[nodo[1]*glxn],U[nodo[1]*glxn+1],
                         U[nodo[2]*glxn],U[nodo[2]*glxn+1]]).reshape([-1,1])
        sig[e] = D[e].dot(B[e].dot(d[e]))
    return sig

def Kel_barra(MN, MC, Ee, Ae, e):
    """
    #
    Resuelve la matriz K_elemental de un elemento 'e' y devuelve también la longitud inicial del elemento
    MN = Coordenadas de cada nodo
    MC = Matriz de conectividad de las barras
    Ee = Modulo de elasticidad de 'e'
    Ae = Sección de 'e'
    e = Nro. de elemento
    #
    """ 
    Le = np.sqrt((MN[MC[e,1],0]-MN[MC[e,0],0])**2+(MN[MC[e,1],1]-MN[MC[e,0],1])**2)
    phi = np.arctan2(MN[MC[e,1],1]-MN[MC[e,0],1],MN[MC[e,1],0]-MN[MC[e,0],0])
    ke = Ee*Ae/Le
    c = np.cos(phi)
    s = np.sin(phi)
    Ke = ke*np.array([[c**2,c*s,-c**2,-c*s],
                   [c*s,s**2,-c*s,-s**2],
                   [-c**2,-c*s,c**2,c*s],
                   [-c*s,-s**2,c*s,s**2]])
    Ke[np.abs(Ke/Ke.max()) < 1e-15] = 0

    return Ke
    
def Kglobal_barra(MN, MC, E, glxn, dimension_elementos, v='None', t='None', A='None'):
    """
    #
    Resuelve la matriz global K
    MN = Coordenadas de cada nodo
    MC = Matriz de conectividad de las barras
    E = Vector Modulos de Elasticidad de cada elementos
    A = Vector Sección de cada elemento
    v = Coeficiente de Poisson
    t = Espesor de los elementos

    #
    """
    Ke = {}  # diccionario para acumular todas las K_elementales
    Nn = MN.shape[0]  # cantidad de nodos
    Ne, Nnxe = MC.shape  # cantidad de elementos
    K = np.zeros([glxn*Nn,glxn*Nn])
    if dimension_elementos==2:
        # especifico para elementos triangulares
        # alpha_e, beta_e, y gamma_e: coef de las funciones de interpolación de cada elemento 'e'
        alpha = np.zeros([3,Ne])
        beta = np.zeros([3,Ne])
        gamma = np.zeros([3,Ne])
        A = np.zeros(Ne)
        B = {}
        D = {}
    
    archivo = 'Matrices.txt'  # Creo archivo para guardar todas las matrices elementales
    with open(archivo,'w') as f:  # la f es como un alias apra el archivo que acabo de abrir
        f.write('Matrices Elementales\n ===============')
        
    for e in range(Ne):
        if dimension_elementos==1:
            if glxn == 1:
                Ke[e] = np.array([[1,-1],[-1,1]])*A*E/(MN[-1]/MC.shape[0])
            elif glxn == 2:
                Ke[e] = Kel_barra(MN, MC, E[e], A[e], e)
        elif dimension_elementos==2:
            nodos = MC[e,:].astype(int)
            alpha[0,e] = MN[nodos[1],0]*MN[nodos[2],1]-MN[nodos[2],0]*MN[nodos[1],1]
            alpha[1,e] = MN[nodos[0],0]*MN[nodos[2],1]-MN[nodos[2],0]*MN[nodos[0],1]
            alpha[2,e] = MN[nodos[0],0]*MN[nodos[1],1]-MN[nodos[1],0]*MN[nodos[0],1]
            beta[0,e] = MN[nodos[1],1]-MN[nodos[2],1]
            beta[1,e] = MN[nodos[2],1]-MN[nodos[0],1]
            beta[2,e] = MN[nodos[0],1]-MN[nodos[1],1]
            gamma[0,e] = MN[nodos[2],0]-MN[nodos[1],0]
            gamma[1,e] = MN[nodos[0],0]-MN[nodos[2],0]
            gamma[2,e] = MN[nodos[1],0]-MN[nodos[0],0]
            A[e] = (alpha[0,e]-alpha[1,e]+alpha[2,e])/2
            B[e] = np.array([
                [beta[0,e],0,beta[1,e],0,beta[2,e],0],
                [0,gamma[0,e],0,gamma[1,e],0,gamma[2,e]],
                [gamma[0,e],beta[0,e],gamma[1,e],beta[1,e],gamma[2,e],beta[2,e]]  
            ])/(2*A[e])
            D[e] = E[e]/(1-v**2)*np.array([[1,v,0],[v,1,0],[0,0,(1-v)/2]])
            Ke[e] = t*np.abs(A[e])*np.transpose(B[e]).dot(D[e].dot(B[e]))        
  
            fe = np.abs(Ke[e].max())
            with open('Matrices.txt','a') as f:  # 'a' de agregar
                f.write(f'\nelemento {e}, fe ={fe:4e}\n')
                f.write(f'{Ke[e]/fe}\n')

            for i in range(Nnxe):
                rangoi = np.linspace(i*glxn,(i+1)*glxn-1,glxn).astype(int)
                rangoni = np.linspace(MC[e,i]*glxn,(MC[e, i]+1)*glxn-1,glxn).astype(int)
                for j in range(Nnxe):
                    rangoj = np.linspace(j*glxn,(j+1)*glxn-1,glxn).astype(int)
                    rangonj = np.linspace(MC[e,j]*glxn,(MC[e, j]+1)*glxn-1,glxn).astype(int)
                    K[np.ix_(rangoni,rangonj)] += Ke[e][np.ix_(rangoi,rangoj)]
    
    fe = np.abs(K.max())
    with open('Matrices.txt','a') as f:  # 'a' de agregar
        f.write(f'\nMatriz Global, fe ={fe:4e}\n')
        f.write(f'{K/fe}\n')
    
    if dimension_elementos == 2:
        return K, Ke, D, B
    elif dimension_elementos == 1:
        return K, Ke

def vector_complemento(s, MN, glxn):
    r = np.array([i for i in range(glxn*MN.shape[0]) if i not in s])
    return r

def dist_uniforme_barra(A, E, C, L, barras, glxn=1, Nnxe=2):
    '''
    #
    Divide un elemento recto en varias barras, devuelve:
    f, d, Rx
    f = fuerza aplicada en los nodos de cada barra
    d = desplazamiento de cada nodo
    tensiones = tension en cada barra
    Rx = Fuerza de reacción en el empotramiento
    
    Se ingresa
    A = sección de la barra
    E = modulo de elasticidad
    C = constante correspondiente a la función distribución de la carga
    L = longitud del elemento
    barras = cantidad de barras en las que partí al elemento
    #
    '''
    MC = np.array([[i, i+1] for i in range(barras)])
    MN = np.linspace(0,L,barras+1).reshape([-1,1])
   
    # Matriz global
    Kglobal = Kglobal_barra(MN, MC, E, A, glxn)[0]
    
    # barra 1
    Ft = 0.5*C*(L/barras)**2  # fuerza total en la barra 1
    f1x = Ft/3  # como se distribuyen las cargas en cada nodo del elemento 1
    f2x = 2*Ft/3  # considerar el area del triangulo

    # el resto de las barras
    f = np.zeros([barras+1]).reshape([-1,1])
    for i in range(barras):
        # Fu -> rectangulo dentro del area, aumenta su magnitud Ft para cada barra 
        Fu = Ft*i
        # Fuerza en nodos de la barra i = suma de todos los rectangulos (Ft*i) + carga de la primer barra(triangulito) (Ft)
        f[i:(i+2)] += np.array([[Fu+f1x],[Fu+f2x]])

    d = np.linalg.solve(Kglobal[:barras,:barras],f[:barras])
    d = np.append(d,np.array([[0]]),0)
    Rx = Kglobal.dot(d)[-1]-f[-1]  # fuerza de reacción en el empotramiento
    
    eps = np.zeros([barras,1])
    tensiones = np.zeros([barras,1])
    for i in range(barras):
        eps[i] = (d[i+1]-d[i])/(L/barras)
        tensiones[i] = eps[i]*E
    
    return f, d, Rx, tensiones, Kglobal