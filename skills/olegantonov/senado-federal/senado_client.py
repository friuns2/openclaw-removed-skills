"""
Cliente async para API de Dados Abertos do Senado Federal.
Base: https://legis.senado.leg.br/dadosabertos

Uso:
    from senate_client import get_senado_client
    
    async def main():
        client = get_senado_client()
        try:
            # Listar senadores atuais
            senators = await client.lista_senadores_atuais()
            
            # Pesquisar matérias
            materias = await client.pesquisar_materia(sigla="PL", ano=2026)
            
            # Votações da semana
            from datetime import date, timedelta
            votacoes = await client.get_votacoes_periodo(
                date.today() - timedelta(days=7),
                date.today()
            )
        finally:
            await client.close()
"""
import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import httpx


# Configurar logger
logger = logging.getLogger(__name__)


# Exceções customizadas
class SenadoAPIError(Exception):
    """Erro base para erros da API do Senado."""
    pass


class SenadoConnectionError(SenadoAPIError):
    """Erro de conexão com a API."""
    pass


class SenadoTimeoutError(SenadoAPIError):
    """Timeout ao conectar com a API."""
    pass


class SenadoNotFoundError(SenadoAPIError):
    """Recurso não encontrado."""
    pass


class SenadoValidationError(SenadoAPIError):
    """Erro de validação de parâmetros."""
    pass


BASE_URL = "https://legis.senado.leg.br/dadosabertos"

# Timeout padrão para requisições (45s)
DEFAULT_TIMEOUT = 45.0


class SenadoClient:
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.client: httpx.AsyncClient | None = None
        self.timeout = timeout

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                base_url=BASE_URL,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True
            )
        return self.client

    async def close(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()

    async def _get(self, path: str, params: dict | None = None, retries: int = 3) -> dict:
        """
        Executa GET com retry logic e tratamento de erros.
        
        Args:
            path: Caminho do endpoint
            params: Parâmetros da query
            retries: Número de tentativas em caso de falha
            
        Raises:
            SenadoTimeoutError: Timeout na requisição
            SenadoNotFoundError: Recurso não encontrado (404)
            SenadoConnectionError: Erro de conexão
            SenadoAPIError: Outros erros da API
        """
        client = await self._get_client()
        last_error = None
        
        for attempt in range(retries):
            try:
                logger.debug(f"Requisição para {path}, tentativa {attempt + 1}/{retries}")
                response = await client.get(path, params=params)
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException as e:
                last_error = SenadoTimeoutError(f"Timeout ao acessar {path}: {e}")
                logger.warning(f"Timeout na tentativa {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise SenadoNotFoundError(f"Recurso não encontrado: {path}")
                last_error = SenadoAPIError(f"Erro HTTP {e.response.status_code}: {e}")
                if e.response.status_code >= 500:
                    logger.warning(f"Erro {e.response.status_code} na tentativa {attempt + 1}/{retries}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                logger.error(f"Erro HTTP: {e}")
                break
                
            except httpx.ConnectError as e:
                last_error = SenadoConnectionError(f"Erro de conexão: {e}")
                logger.warning(f"Erro de conexão na tentativa {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                last_error = SenadoAPIError(f"Erro inesperado: {e}")
                logger.error(f"Erro inesperado: {e}")
                break
        
        if last_error:
            raise last_error
        
        raise SenadoAPIError("Falha após todas as tentativas")

    async def _get_list(self, path: str, params: dict | None = None) -> list:
        """Executa GET e retorna lista, lidando com estrutura variável."""
        data = await self._get(path, params)
        
        # Navega pelo JSON para encontrar a lista
        def find_list(obj: Any) -> list | None:
            if obj is None:
                return None
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                for value in obj.values():
                    result = find_list(value)
                    if result is not None:
                        return result
            return None
        
        result = find_list(data)
        return result if result else []

    # ========== PLENÁRIO ==========

    async def get_agenda_plenario_dia(self, data: date | None = None) -> dict:
        """Agenda do plenário para um dia específico (YYYYMMDD)."""
        if data is None:
            data = date.today()
        data_str = data.strftime("%Y%m%d")
        return await self._get(f"/plenario/agenda/dia/{data_str}.json")

    async def get_agenda_plenario_mes(self, ano: int, mes: int) -> dict:
        """Agenda do plenário para um mês (YYYYMM)."""
        yyyymm = f"{ano}{mes:02d}"
        return await self._get(f"/plenario/agenda/mes/{yyyymm}.json")

    async def get_votacoes_periodo(self, data_inicio: date, data_fim: date) -> list[dict]:
        """Lista de votações em um período."""
        inicio = data_inicio.strftime("%Y%m%d")
        fim = data_fim.strftime("%Y%m%d")
        data = await self._get(f"/plenario/lista/votacao/{inicio}/{fim}.json")
        votacoes = data.get("ListaVotacoes", {}).get("Votacoes", {}).get("Votacao", [])
        return votacoes if isinstance(votacoes, list) else [votacoes] if votacoes else []

    # ========== COMISSÕES ==========

    async def get_agenda_comissao_dia(self, data: date | None = None) -> dict:
        """Agenda das comissões para um dia."""
        if data is None:
            data = date.today()
        data_str = data.strftime("%Y%m%d")
        return await self._get(f"/comissao/agenda/dia/{data_str}.json")

    async def get_agenda_comissao_periodo(self, data_inicio: date, data_fim: date) -> dict:
        """Agenda das comissões em um período."""
        inicio = data_inicio.strftime("%Y%m%d")
        fim = data_fim.strftime("%Y%m%d")
        return await self._get(f"/comissao/agenda/{inicio}/{fim}.json")

    async def get_lista_comissoes(self) -> list[dict]:
        """Lista de todas as comissões."""
        data = await self._get("/comissao/lista.json")
        comissoes = data.get("ListaComissoes", {}).get("Comissoes", {}).get("Comissao", [])
        return comissoes if isinstance(comissoes, list) else [comissoes] if comissoes else []

    # ========== SENADORES ==========

    async def lista_senadores_atuais(self) -> list[dict]:
        """Lista de senadores em exercício."""
        data = await self._get("/senador/lista/atual.json")
        return data.get("ListaParlamentarEmExercicio", {}).get("Parlamentares", {}).get("Parlamentar", [])

    async def buscar_senador_por_nome(self, nome: str) -> list[dict]:
        """Busca senadores pelo nome (contém)."""
        todos = await self.lista_senadores_atuais()
        nome_lower = nome.lower()
        return [s for s in todos if nome_lower in s.get("IdentificacaoParlamentar", {}).get("NomeParlamentar", "").lower()]

    async def get_senador_detalhe(self, codigo: str) -> dict | None:
        """Detalhe de um senador pelo código."""
        data = await self._get(f"/senador/{codigo}.json")
        return data.get("DetalheParlamentar", {}).get("Parlamentar")

    async def get_autorias_senador(self, codigo: str) -> list[dict]:
        """Lista de autorias de um senador."""
        data = await self._get(f"/senador/{codigo}/autorias.json")
        autorias = data.get("ListaAutoriasParlamentar", {}).get("Autorias", {}).get("Autoria", [])
        return autorias if isinstance(autorias, list) else [autorias] if autorias else []

    async def get_discursos_senador(self, codigo: str, data_inicio: date | None = None, data_fim: date | None = None) -> list[dict]:
        """Discursos de um senador em um período."""
        params = {}
        if data_inicio:
            params["dataIni"] = data_inicio.strftime("%Y%m%d")
        if data_fim:
            params["dataFim"] = data_fim.strftime("%Y%m%d")
        data = await self._get(f"/senador/{codigo}/discursos.json", params)
        return data.get("ListaDiscursos", {}).get("Discursos", {}).get("Discurso", [])

    async def get_senador_filiacoes(self, codigo: str) -> list[dict]:
        """Filiações partidárias de um senador."""
        data = await self._get(f"/senador/{codigo}/filiacoes.json")
        filiacoes = data.get("FiliacaoParlamentar", {}).get("Parlamentar", {}).get("Filiacoes", {}).get("Filiacao", [])
        return filiacoes if isinstance(filiacoes, list) else [filiacoes] if filiacoes else []

    async def get_senador_cargos(self, codigo: str) -> list[dict]:
        """Cargos exercidos por um senador."""
        data = await self._get(f"/senador/{codigo}/cargos.json")
        cargos = data.get("CargoParlamentar", {}).get("Parlamentar", {}).get("Cargos", {}).get("Cargo", [])
        return cargos if isinstance(cargos, list) else [cargos] if cargos else []

    async def get_senador_liderancas(self, codigo: str) -> list[dict]:
        """Lideranças exercidas por um senador."""
        data = await self._get(f"/senador/{codigo}/liderancas.json")
        liderancas = data.get("LiderancaParlamentar", {}).get("Parlamentar", {}).get("Liderancas", {}).get("Lideranca", [])
        return liderancas if isinstance(liderancas, list) else [liderancas] if liderancas else []

    async def get_senador_apartes(self, codigo: str) -> list[dict]:
        """Apartes (intervenções) de um senador."""
        data = await self._get(f"/senador/{codigo}/apartes.json")
        apartes = data.get("ApartesParlamentar", {}).get("Parlamentar", {}).get("Apartes", {}).get("Aparte", [])
        return apartes if isinstance(apartes, list) else [apartes] if apartes else []

    async def get_senador_relatorias(self, codigo: str) -> list[dict]:
        """Relatorias de um senador."""
        data = await self._get(f"/senador/{codigo}/relatorias.json")
        relatorias = data.get("RelatoriaParlamentar", {}).get("Parlamentar", {}).get("Relatorias", {}).get("Relatoria", [])
        return relatorias if isinstance(relatorias, list) else [relatorias] if relatorias else []

    async def get_senador_profissao(self, codigo: str) -> list[dict]:
        """Profissão de um senador."""
        return await self._get_list(f"/senador/{codigo}/profissao.json")

    async def get_senador_historico_academico(self, codigo: str) -> list[dict]:
        """Histórico acadêmico de um senador."""
        return await self._get_list(f"/senador/{codigo}/historicoAcademico.json")

    async def get_senador_licencas(self, codigo: str) -> list[dict]:
        """Licenças de um senador."""
        return await self._get_list(f"/senador/{codigo}/licencas.json")

    # ========== MATÉRIAS / PROPOSIÇÕES ==========

    async def pesquisar_materia(self, sigla: str | None = None, numero: str | None = None, ano: int | None = None, tramitando: bool = True) -> list[dict]:
        """Pesquisa matérias por sigla, número e ano."""
        params: dict[str, Any] = {}
        if sigla:
            params["sigla"] = sigla
        if numero:
            params["numero"] = numero
        if ano:
            params["ano"] = str(ano)
        if tramitando:
            params["tramitando"] = "S"
        
        data = await self._get("/materia/pesquisa/lista.json", params)
        materias = data.get("PesquisaBasicaMateria", {}).get("Materias", {}).get("Materia", [])
        return materias if isinstance(materias, list) else [materias] if materias else []

    async def get_materia_detalhe(self, codigo: str) -> dict | None:
        """Detalhe de uma matéria pelo código."""
        data = await self._get(f"/materia/{codigo}.json")
        return data.get("DetalheMateria", {}).get("Materia")

    async def get_materia_movimentacoes(self, codigo: str) -> list[dict]:
        """Movimentações de uma matéria."""
        data = await self._get(f"/materia/movimentacoes/{codigo}.json")
        movimentacoes = data.get("MovimentacaoMateria", {}).get("Movimentacao", [])
        return movimentacoes if isinstance(movimentacoes, list) else [movimentacoes] if movimentacoes else []

    async def get_materia_tramitacao(self, codigo: str) -> list[dict]:
        """Tramitações de uma matéria."""
        data = await self._get(f"/materia/tramitacao/{codigo}.json")
        tramitacoes = data.get("TramitacaoMateria", {}).get("Tramitacao", [])
        return tramitacoes if isinstance(tramitacoes, list) else [tramitacoes] if tramitacoes else []

    # ========== NOVOS ENDPOINTS ==========

    async def get_senador_votacoes(self, codigo: str) -> list[dict]:
        """Histórico de votações de um senador."""
        data = await self._get(f"/senador/{codigo}/votacoes.json")
        votacoes = data.get("VotacaoParlamentar", {}).get("Votacoes", {}).get("Votacao", [])
        return votacoes if isinstance(votacoes, list) else [votacoes] if votacoes else []

    async def get_senador_comissoes(self, codigo: str) -> list[dict]:
        """Comissões de que um senador é membro."""
        data = await self._get(f"/senador/{codigo}/comissoes.json")
        comissoes = data.get("MembroComissaoParlamentar", {}).get("Comissoes", {}).get("Comissao", [])
        return comissoes if isinstance(comissoes, list) else [comissoes] if comissoes else []

    async def get_senador_mandatos(self, codigo: str) -> list[dict]:
        """Mandatos de um senador."""
        data = await self._get(f"/senador/{codigo}/mandatos.json")
        mandatos = data.get("MandatoParlamentar", {}).get("Mandatos", {}).get("Mandato", [])
        return mandatos if isinstance(mandatos, list) else [mandatos] if mandatos else []

    async def get_materia_por_sigla(self, sigla: str, numero: str, ano: int) -> dict | None:
        """Busca matéria pela sigla completa (ex: PL 1234/2026)."""
        resultados = await self.pesquisar_materia(sigla=sigla, numero=numero, ano=ano, tramitando=False)
        return resultados[0] if resultados else None

    async def pesquisar_materia_por_assunto(self, assunto: str, tramitando: bool = True) -> list[dict]:
        """Pesquisa matérias por assunto/keyword."""
        params: dict[str, Any] = {"assunto": assunto}
        if tramitando:
            params["tramitando"] = "S"
        data = await self._get("/materia/pesquisa/lista.json", params)
        materias = data.get("PesquisaBasicaMateria", {}).get("Materias", {}).get("Materia", [])
        return materias if isinstance(materias, list) else [materias] if materias else []

    async def get_materia_situacao_atual(self, codigo: str) -> dict:
        """Situação atual de uma matéria."""
        return await self._get(f"/materia/situacaoatual/{codigo}.json")

    async def get_materia_textos(self, codigo: str) -> list[dict]:
        """Textos de uma matéria."""
        return await self._get_list(f"/materia/textos/{codigo}.json")

    async def get_materia_emendas(self, codigo: str) -> list[dict]:
        """Emendas de uma matéria."""
        return await self._get_list(f"/materia/emendas/{codigo}.json")

    async def get_materia_relatorias(self, codigo: str) -> list[dict]:
        """Relatorias de uma matéria."""
        return await self._get_list(f"/materia/relatorias/{codigo}.json")

    async def get_materia_autoria(self, codigo: str) -> list[dict]:
        """Autoria de uma matéria."""
        return await self._get_list(f"/materia/autoria/{codigo}.json")

    async def get_materias_tramitando(self) -> list[dict]:
        """Matérias atualmente em tramitação."""
        return await self._get_list("/materia/tramitando.json")

    async def get_materias_atualizadas(self, dias: int = 7) -> list[dict]:
        """Matérias atualizadas nos últimos N dias."""
        return await self._get_list("/materia/atualizadas.json", {"numdias": dias})

    # ========== PLENÁRIO (RESULTADOS E VOTAÇÕES) ==========

    async def get_resultado_plenario_dia(self, data: date) -> dict:
        """Resultado do plenário em um dia."""
        data_str = data.strftime("%Y%m%d")
        return await self._get(f"/plenario/resultado/{data_str}.json")

    async def get_resultado_plenario_mes(self, ano: int, mes: int) -> dict:
        """Resultado do plenário em um mês."""
        return await self._get(f"/plenario/resultado/mes/{ano}{mes:02d}.json")

    async def get_votacoes_nominais_ano(self, ano: int) -> list[dict]:
        """Todas as votações nominais de um ano."""
        return await self._get_list(f"/plenario/votacao/nominal/{ano}.json")

    async def get_discursos_plenario(self, data_inicio: date, data_fim: date) -> list[dict]:
        """Discursos em plenário em um período."""
        inicio = data_inicio.strftime("%Y%m%d")
        fim = data_fim.strftime("%Y%m%d")
        return await self._get_list(f"/plenario/lista/discursos/{inicio}/{fim}.json")

    async def get_encontro_plenario(self, codigo: str) -> dict:
        """Detalhes de uma sessão/encontro plenário."""
        return await self._get(f"/plenario/encontro/{codigo}.json")

    async def get_encontro_pauta(self, codigo: str) -> list[dict]:
        """Pauta de uma sessão/encontro plenário."""
        return await self._get_list(f"/plenario/encontro/{codigo}/pauta.json")

    # ========== COMISSÕES (DETALHE) ==========

    async def get_comissao_detalhe(self, codigo: str) -> dict:
        """Detalhes de uma comissão."""
        return await self._get(f"/comissao/{codigo}.json")

    async def get_comissao_reuniao(self, codigo_reuniao: str) -> dict:
        """Detalhes de uma reunião de comissão."""
        return await self._get(f"/comissao/reuniao/{codigo_reuniao}.json")

    async def get_composicao_comissao(self, codigo: str) -> list[dict]:
        """Composição (membros) de uma comissão."""
        return await self._get_list(f"/composicao/comissao/{codigo}.json")

    async def get_lista_comissoes_mistas(self) -> list[dict]:
        """Lista de comissões mistas (CN)."""
        return await self._get_list("/comissao/lista/mistas.json")

    # ========== VOTAÇÃO EM COMISSÕES ==========

    async def get_votacao_comissao(self, sigla_comissao: str) -> list[dict]:
        """Votações em uma comissão."""
        return await self._get_list(f"/votacaoComissao/comissao/{sigla_comissao}.json")

    async def get_votacao_comissao_materia(self, sigla: str, numero: str, ano: int) -> list[dict]:
        """Votações em comissão sobre uma matéria."""
        return await self._get_list(f"/votacaoComissao/materia/{sigla}/{numero}/{ano}.json")

    async def get_votacao_comissao_parlamentar(self, codigo: str) -> list[dict]:
        """Votações de um parlamentar em comissões."""
        return await self._get_list(f"/votacaoComissao/parlamentar/{codigo}.json")

    # ========== COMPOSIÇÃO E LIDERANÇAS ==========

    async def get_mesa_senado(self) -> dict:
        """Mesa diretora do Senado."""
        return await self._get("/composicao/mesaSF.json")

    async def get_mesa_congresso(self) -> dict:
        """Mesa do Congresso Nacional."""
        return await self._get("/composicao/mesaCN.json")

    async def get_liderancas(self) -> dict:
        """Lideranças partidárias."""
        return await self._get("/composicao/lideranca.json")

    async def get_blocos_parlamentares(self) -> list[dict]:
        """Blocos parlamentares."""
        return await self._get_list("/composicao/lista/blocos.json")

    # ========== PROCESSO ==========

    async def get_processo(self, codigo: str) -> dict:
        """Processo legislativo completo de uma matéria.
        Retorna autuações, situações, tramitação em estrutura rica.
        Endpoint preferido sobre /materia/{codigo} para status detalhado.
        """
        return await self._get(f"/processo/{codigo}.json")

    # ========== AUTORES, LEGISLAÇÃO, DISCURSO ==========

    async def get_autores_atuais(self) -> list[dict]:
        """Lista de autores (senadores atuais como autores)."""
        return await self._get_list("/autor/lista/atual.json")

    async def pesquisar_legislacao(self, tipo: str | None = None, ano: int | None = None, numero: str | None = None) -> list[dict]:
        """Pesquisa legislação/normas."""
        params: dict[str, Any] = {}
        if tipo:
            params["tipo"] = tipo
        if ano:
            params["ano"] = str(ano)
        if numero:
            params["numero"] = numero
        return await self._get_list("/legislacao/lista.json", params)

    async def get_discurso_texto_integral(self, codigo_pronunciamento: str) -> dict:
        """Texto integral de um discurso/pronunciamento."""
        return await self._get(f"/discurso/texto-integral/{codigo_pronunciamento}.json")

    # ========== UTILITÁRIOS ==========

    async def get_materias_recentes(self, dias: int = 7) -> list[dict]:
        """Busca matérias apresentadas nos últimos N dias."""
        hoje = date.today()
        inicio = hoje - timedelta(days=dias)
        data_str = inicio.strftime("%Y%m%d")
        
        data = await self._get("/materia/pesquisa/lista.json", {
            "dataApresentacaoIni": data_str,
            "tramitando": "S",
            "itens": 50
        })
        materias = data.get("PesquisaBasicaMateria", {}).get("Materias", {}).get("Materia", [])
        return materias if isinstance(materias, list) else [materias] if materias else []

    async def get_votacoes_semana(self) -> list[dict]:
        """Votações da última semana."""
        return await self.get_votacoes_periodo(date.today() - timedelta(days=7), date.today())

    async def get_agenda_semana(self) -> list:
        """Agenda do plenário para a semana atual."""
        hoje = date.today()
        dia_semana = hoje.weekday()
        inicio = hoje - timedelta(days=dia_semana)
        fim = inicio + timedelta(days=6)
        
        # Baixa mês a mês
        meses: dict[str, list] = {}
        cursor = date(inicio.year, inicio.month, 1)
        fim_mes = date(fim.year, fim.month, 1)
        
        all_events = []
        while cursor <= fim_mes:
            key = f"{cursor.year}{cursor.month:02d}"
            meses[key] = await self.get_agenda_plenario_mes(cursor.year, cursor.month)
            
            # Extrai eventos do mês
            mes_data = meses[key]
            def extract_events(obj: Any) -> list:
                if isinstance(obj, list):
                    return obj
                if isinstance(obj, dict):
                    for v in obj.values():
                        result = extract_events(v)
                        if result:
                            return result
                return []
            
            all_events.extend(extract_events(mes_data))
            cursor = date(cursor.year, cursor.month + 1, 1) if cursor.month < 12 else date(cursor.year + 1, 1, 1)
        
        return all_events


# Instância global
_client: SenadoClient | None = None


def get_senado_client() -> SenadoClient:
    """Retorna instância singleton do cliente."""
    global _client
    if _client is None:
        _client = SenadoClient()
    return _client


async def close_senado_client():
    """Fecha o cliente global."""
    global _client
    if _client:
        await _client.close()
        _client = None


# ========== FACADE FUNCTIONS (uso direto) ==========

async def lista_senadores_atuais() -> list[dict]:
    """Facade: lista de senadores atuais."""
    client = get_senado_client()
    return await client.lista_senadores_atuais()


async def buscar_senador(nome: str) -> list[dict]:
    """Facade: busca senador por nome."""
    client = get_senado_client()
    return await client.buscar_senador_por_nome(nome)


async def pesquisar_materia(sigla: str | None = None, numero: str | None = None, ano: int | None = None) -> list[dict]:
    """Facade: pesquisa matéria."""
    client = get_senado_client()
    return await client.pesquisar_materia(sigla, numero, ano)


async def get_votacoes_semana() -> list[dict]:
    """Facade: votações da semana."""
    client = get_senado_client()
    return await client.get_votacoes_semana()


async def get_materias_recentes(dias: int = 7) -> list[dict]:
    """Facade: matérias recentes."""
    client = get_senado_client()
    return await client.get_materias_recentes(dias)
