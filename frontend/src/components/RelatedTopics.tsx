type Topic = { topic: string; citation_ids: string[] };

type Props = {
  topics: Topic[];
  onSelect?: (topic: string) => void;
};

function RelatedTopics({ topics, onSelect }: Props) {
  if (!topics.length) return null;

  return (
    <section className="related-panel">
      <h3>Related topics</h3>
      <ul className="topic-list">
        {topics.map((item) => (
          <li key={item.topic}>
            <button className="topic-button" onClick={() => onSelect?.(item.topic)} type="button">
              {item.topic}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default RelatedTopics;