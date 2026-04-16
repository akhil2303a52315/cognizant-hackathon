import { motion } from "framer-motion"
import { CheckCircle2 } from "lucide-react"
import ModelBadge from "./ModelBadge"

interface Agent {
  id: string
  name: string
  tagline: string
  emoji: string
  role: string
  model: string
  modelProvider: string
  modelColor: string
  modelIcon: string
  accentColor: string
}

interface AgentCardProps {
  agent: Agent
  isSelected: boolean
  agentConfidence: Record<string, number>
  handleSelectAgent: (id: string) => void
}

const AgentCard = ({ agent, isSelected, agentConfidence, handleSelectAgent }: AgentCardProps) => {
  return (
    <motion.div
      layout
      layoutId={`agent-card-${agent.id}`}
      initial={{ scale: 1 }}
      animate={isSelected ? {
        scale: 1.03,
        transition: { type: "spring", stiffness: 300, damping: 20 }
      } : { scale: 1 }}
      whileHover={{ scale: isSelected ? 1.03 : 1.015, y: -2 }}
      className={`
        relative p-4 rounded-2xl cursor-pointer
        transition-all duration-300 ease-in-out
        ${isSelected ? `
          border-[1.5px]
          shadow-2xl
        ` : `
          border
          border-white/10
          bg-white/[0.03]
          hover:bg-white/[0.06]
          hover:border-white/20
        `}
      `}
      style={isSelected ? {
        background: `linear-gradient(135deg, 
          rgba(255,255,255,0.08) 0%, 
          rgba(255,255,255,0.04) 100%)`,
        backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)",
        borderColor: agent.accentColor + "80",
        boxShadow: `
          0 8px 32px rgba(0, 0, 0, 0.4),
          0 0 0 1px ${agent.accentColor}30,
          0 0 30px ${agent.accentColor}20,
          inset 0 1px 0 rgba(255,255,255,0.1)
        `,
      } : {}}
      onClick={() => handleSelectAgent(agent.id)}
    >
      {/* ANIMATED SHIMMER BORDER — only when selected */}
      {isSelected && (
        <motion.div
           className="absolute inset-0 rounded-2xl pointer-events-none"
           style={{
             background: `linear-gradient(90deg, 
               transparent, 
               ${agent.accentColor}30, 
               transparent)`,
             backgroundSize: "200% 100%",
           }}
           animate={{ backgroundPosition: ["200% 0", "-200% 0"] }}
           transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
      )}

      {/* SELECTED BADGE — top right */}
      {isSelected && (
        <motion.div
          initial={{ opacity: 0, scale: 0.5, y: -5 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 15 }}
          className="
            absolute -top-2 -right-2 z-10
            flex items-center gap-1 px-2 py-0.5
            rounded-full text-[10px] font-bold
            bg-emerald-500/20 border border-emerald-400/50
            text-emerald-400 shadow-lg shadow-emerald-900/30
          "
        >
          <CheckCircle2 className="w-2.5 h-2.5" />
          Active
        </motion.div>
      )}

      {/* GLOWING LEFT ACCENT BAR — only when selected */}
      {isSelected && (
        <div
          className="absolute left-0 top-4 bottom-4 w-[3px] rounded-r-full"
          style={{
            background: `linear-gradient(180deg, 
              ${agent.accentColor}, 
              ${agent.accentColor}60)`,
            boxShadow: `0 0 12px ${agent.accentColor}80`,
          }}
        />
      )}

      {/* CARD CONTENT */}
      <div className="flex items-start gap-3 pl-2">
        
        {/* AGENT ICON */}
        <div
          className="
            flex-shrink-0 w-10 h-10 rounded-xl
            flex items-center justify-center text-lg
            border border-white/10
          "
          style={{
            background: isSelected 
              ? `linear-gradient(135deg, ${agent.accentColor}30, ${agent.accentColor}10)`
              : "rgba(255,255,255,0.05)",
            boxShadow: isSelected 
              ? `0 0 16px ${agent.accentColor}30` 
              : "none"
          }}
        >
          {agent.emoji}
        </div>

        <div className="flex-1 min-w-0">
          
          {/* AGENT NAME */}
          <h3
            className="font-bold text-[15px] leading-tight tracking-tight font-outfit"
            style={{
              color: isSelected ? "#ffffff" : "rgba(255,255,255,0.85)",
              textShadow: isSelected 
                ? `0 0 20px ${agent.accentColor}60` 
                : "none"
            }}
          >
            {agent.name}
          </h3>

          {/* AGENT TAGLINE */}
          <p
            className="text-[11px] mt-0.5 leading-snug"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: isSelected 
                ? "rgba(255,255,255,0.65)" 
                : "rgba(255,255,255,0.4)",
              fontStyle: "italic"
            }}
          >
            "{agent.tagline}"
          </p>

          {/* ROLE CHIP */}
          <div className="mt-1.5">
            <span
              className="
                text-[9px] uppercase font-semibold tracking-widest
                px-2 py-0.5 rounded-md
              "
              style={{
                color: agent.accentColor,
                backgroundColor: `${agent.accentColor}15`,
                border: `1px solid ${agent.accentColor}25`,
              }}
            >
              {agent.role.split("+")[0]?.trim() ?? agent.role}
            </span>
          </div>

          {/* MODEL BADGE */}
          <ModelBadge
            model={agent.model}
            modelProvider={agent.modelProvider}
            modelColor={agent.modelColor}
            modelIcon={agent.modelIcon}
          />

        </div>
      </div>

      {/* CONFIDENCE BAR — only when selected AND agent has run */}
      {isSelected && agentConfidence[agent.id] && (
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-3 ml-2"
        >
          <div className="flex justify-between items-center mb-1">
            <span className="text-[9px] uppercase tracking-widest text-white/40 font-semibold">
              Confidence
            </span>
            <span 
              className="text-[11px] font-bold"
              style={{ color: agent.accentColor }}
            >
              {agentConfidence[agent.id]}%
            </span>
          </div>
          <div className="h-1 w-full rounded-full bg-white/10">
            <motion.div
              className="h-1 rounded-full"
              style={{
                background: `linear-gradient(90deg, 
                  ${agent.accentColor}, 
                  ${agent.accentColor}80)`,
                width: `${agentConfidence[agent.id]}%`,
                boxShadow: `0 0 8px ${agent.accentColor}60`
              }}
              initial={{ width: "0%" }}
              animate={{ width: `${agentConfidence[agent.id]}%` }}
              transition={{ duration: 1, delay: 0.3 }}
            />
          </div>
        </motion.div>
      )}

    </motion.div>
  )
}

export default AgentCard
