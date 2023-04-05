import {IconArrowRight, IconBolt, IconSearch} from "@tabler/icons-react";
import {FC, KeyboardEvent, useEffect, useRef, useState} from "react";
import {Source} from "../types";

interface SearchProps {
    onSearch: (searchResult: string) => void;
    onAnswerUpdate: (answer: string) => void;
    onSources: (sources: Source[]) => void;
    onDone: (done: boolean) => void;
}

let endpoint = "ws://localhost:8000/chat";
if (window.location.hostname.indexOf("rentagpt.com") === 0) {
    endpoint = "ws://rentagpt.com/chat";
} else if (window.location.hostname.indexOf("rentagpt.fly.dev") === 0) {
    endpoint = "ws://rentagpt.fly.dev/chat";
}

export const Search: FC<SearchProps> = ({onSearch, onAnswerUpdate, onSources, onDone}) => {
    const inputRef = useRef<HTMLInputElement>(null);

    const [query, setQuery] = useState<string>("");
    const [apiKey, setApiKey] = useState<string>("");
    const [showSettings, setShowSettings] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);

    const handleSearch = async () => {
        if (!query) {
            alert("Escribe alguna pregunta");
            return;
        }
        setLoading(true);
        onSearch(query);
        await handleQuery();
    };

    const handleQuery = async () => {
        const ws = new WebSocket(endpoint);
        ws.onopen = (event) => {
            ws.send(JSON.stringify({query, apiKey}));
        };

        ws.onmessage = (e) => {
            const message = JSON.parse(e.data);
            if (message.sender === "bot") {
                if (message.type === "info") {
                    const {sources}: { sources: Source[] } = JSON.parse(message.message);
                    onSources(sources);
                } else if (message.type === "stream") {
                    onAnswerUpdate(message.message);
                } else if (message.type === "end") {
                    onDone(true);
                }
            }
        };
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleSearch();
        }
    };

    const handleSave = () => {
        if (apiKey.length !== 51) {
            alert("Entra una API key válida.");
            return;
        }

        localStorage.setItem("OPENAI_API_KEY", apiKey);

        setShowSettings(false);
        inputRef.current?.focus();
    };

    const handleClear = () => {
        localStorage.removeItem("OPENAI_API_KEY");

        setApiKey("");
    };

    useEffect(() => {
        const OPENAI_API_KEY = localStorage.getItem("OPENAI_API_KEY");

        if (OPENAI_API_KEY) {
            setApiKey(OPENAI_API_KEY);
        } else {
            setShowSettings(true);
        }

        inputRef.current?.focus();
    }, []);

    return (
        <>
            {loading ? (
                <div className="flex items-center justify-center pt-64 sm:pt-72 flex-col">
                    <div
                        className="inline-block h-16 w-16 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
                    <div className="mt-8 text-2xl">Generando respuesta...</div>
                </div>
            ) : (
                <div
                    className="mx-auto flex h-full w-full max-w-[750px] flex-col items-center space-y-6 px-3 pt-32 sm:pt-64">
                    <div className="flex items-center">
                        <IconBolt size={36}/>
                        <div className="ml-1 text-center text-4xl">RentaGPT</div>
                    </div>

                    {apiKey.length === 51 ? (
                        <div className="relative w-full">
                            <IconSearch
                                className="text=[#D4D4D8] absolute top-3 w-10 left-1 h-6 rounded-full opacity-50 sm:left-3 sm:top-4 sm:h-8"/>

                            <input
                                ref={inputRef}
                                className="h-12 w-full rounded-full border border-zinc-600 bg-[#2A2A31] pr-12 pl-11 focus:border-zinc-800 focus:bg-[#18181C] focus:outline-none focus:ring-2 focus:ring-zinc-800 sm:h-16 sm:py-2 sm:pr-16 sm:pl-16 sm:text-lg"
                                type="text"
                                placeholder="Pregunta cualquier duda relacionada con la Renta 2022..."
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />

                            <button>
                                <IconArrowRight
                                    onClick={handleSearch}
                                    className="absolute right-2 top-2.5 h-7 w-7 rounded-full bg-blue-500 p-1 hover:cursor-pointer hover:bg-blue-600 sm:right-3 sm:top-3 sm:h-10 sm:w-10"
                                />
                            </button>
                        </div>
                    ) : (
                        <div className="text-center text-[#D4D4D8]">Escribe tu API key OpenAI.</div>
                    )}

                    <button
                        className="flex cursor-pointer items-center space-x-2 rounded-full border border-zinc-600 px-3 py-1 text-sm text-[#D4D4D8] hover:text-white"
                        onClick={() => setShowSettings(!showSettings)}
                    >
                        {showSettings ? "Ocultar" : "Mostrar"} Configuración
                    </button>

                    {showSettings && (
                        <>
                            <input
                                type="password"
                                className="max-w-[400px] block w-full rounded-md border border-gray-300 p-2 text-black shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 sm:text-sm"
                                value={apiKey}
                                onChange={(e) => {
                                    setApiKey(e.target.value);

                                    if (e.target.value.length !== 51) {
                                        setShowSettings(true);
                                    }
                                }}
                            />

                            <div className="flex space-x-2">
                                <div
                                    className="flex cursor-pointer items-center space-x-2 rounded-full border border-zinc-600 bg-blue-500 px-3 py-1 text-sm text-white hover:bg-blue-600"
                                    onClick={handleSave}
                                >
                                    Guardar
                                </div>

                                <div
                                    className="flex cursor-pointer items-center space-x-2 rounded-full border border-zinc-600 bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
                                    onClick={handleClear}
                                >
                                    Borrar
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </>
    );
};
