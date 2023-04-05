import React, {useState} from 'react'
import {Answer} from "./components/Answer";
import {Search} from "./components/Search";
import {Source} from "./types";

function App() {
    const [query, setQuery] = useState<string>("");
    const [answer, setAnswer] = useState<string>("");
    const [sources, setSources] = useState<Source[]>([]);
    const [done, setDone] = useState<boolean>(false);

    return (
        <div className="h-screen overflow-auto bg-[#18181C] text-[#D4D4D8]">
            {answer ? (
                <Answer
                    query={query}
                    answer={answer}
                    sources={sources}
                    done={done}
                    onReset={() => {
                        setQuery("");
                        setAnswer("");
                        setSources([])
                        setDone(false);
                    }}
                />
            ) : (
                <Search
                    onSearch={setQuery}
                    onAnswerUpdate={(value) => setAnswer((prev) => prev + value)}
                    onSources={setSources}
                    onDone={setDone}
                />
            )}
        </div>
    )
}

export default App
