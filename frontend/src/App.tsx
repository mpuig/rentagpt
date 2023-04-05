import React, {useState} from 'react'
import { IconBrandGithub, IconBrandTwitter } from "@tabler/icons-react";
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
            <a
                className="absolute top-0 right-12 p-4 cursor-pointer"
                href="https://twitter.com/mpuig"
                target="_blank"
                rel="noreferrer"
            >
                <IconBrandTwitter/>
            </a>

            <a
                className="absolute top-0 right-2 p-4 cursor-pointer"
                href="https://github.com/mpuig/rentagpt"
                target="_blank"
                rel="noreferrer"
            >
                <IconBrandGithub/>
            </a>

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
