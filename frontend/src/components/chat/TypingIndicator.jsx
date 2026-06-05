import { motion } from "framer-motion";

const Dot = ({ delay }) => (
  <motion.span
    className="w-2 h-2 rounded-full bg-blue-500"
    animate={{
      y: [0, -6, 0],
    }}
    transition={{
      duration: 0.6,
      repeat: Infinity,
      delay,
    }}
  />
);

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 p-3">
      <div className="bg-white dark:bg-slate-800 rounded-2xl px-4 py-3 shadow flex gap-2">
        <Dot delay={0} />
        <Dot delay={0.2} />
        <Dot delay={0.4} />
      </div>
    </div>
  );
}
