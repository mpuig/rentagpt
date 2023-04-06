import {IconReload} from "@tabler/icons-react";
import {FC} from "react";
import {Source} from "../types";

interface AnswerProps {
  query: string;
  answer: string;
  sources: Source[];
  done: boolean;
  onReset: () => void;
}

export const Answer: FC<AnswerProps> = ({ query, sources, answer, done, onReset }) => {
  return (
    <div className="max-w-[1000px] space-y-4 py-16 px-8 sm:px-24 sm:pt-16 pb-32">
      <div className="text-2xl sm:text-4xl">{query}</div>

      <div className="border-b border-zinc-800 pb-4">
        <div className="text-md text-blue-500">Respuesta</div>
        <div className="mt-2 overflow-auto">{replaceSourcesWithLinks(answer, sources)}</div>
      </div>

      {done && (
        <>
          <div className="border-b border-zinc-800 pb-4">
            <div className="text-md text-blue-500">Fuentes</div>

            {Array.isArray(sources) && sources.map((source, index) => (
              <div
                key={index}
                className="mt-1 overflow-auto"
              >
                • {`[${index + 1}] `}
                <a
                  className="hover:cursor-pointer hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                  href={source.source}
                >
                  {source.source.split("//")[1].split("/")[0].replace("www.", "")}
                </a>
              </div>
            ))}
          </div>

          <button
            className="flex h-10 w-52 items-center justify-center rounded-full bg-blue-500 p-2 hover:cursor-pointer hover:bg-blue-600"
            onClick={onReset}
          >
            <IconReload size={18} />
            <div className="ml-2">Hacer otra pregunta</div>
          </button>
            <p className="text-xs">
                RentaGPT usa Inteligencia Artificial (GPT-3) para responder cualquier pregunta relacionada con el
                <a href="https://sede.agenciatributaria.gob.es/Sede/Ayuda/22Manual/100.html" className="more-info"
                   target="_blank">Manual Práctico de Renta 2022</a>.

            </p>
            <p className="text-xs">
                Es un proyecto experimental y puede producir información inexacta.
            </p>
        </>
      )}
    </div>
  );
};

const replaceSourcesWithLinks = (answer: string, sourceLinks: Source[]) => {
  const elements = answer.split(/(\[[0-9]+\])/).map((part, index) => {
    if (/\[[0-9]+\]/.test(part)) {
      const link = sourceLinks[parseInt(part.replace(/[\[\]]/g, "")) - 1];

      return link && (
        <a
          key={index}
          className="hover:cursor-pointer text-blue-500"
          href={link.source}
          target="_blank"
          rel="noopener noreferrer"
        >
          {part}
        </a>
      );
    } else {
      return part;
    }
  });

  return elements;
};
