import { motion } from "framer-motion"
import { CheckCircle2, Lock, LucideIcon } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface RoundTabProps {
  number: number
  label: string
  sublabel: string
  icon: LucideIcon
  description: string
  isCompleted: boolean
  isActive: boolean
  isLocked: boolean
  onClick: () => void
}

const RoundTab = ({ 
  number, 
  label, 
  sublabel, 
  icon: IconComponent, 
  isCompleted, 
  isActive, 
  isLocked, 
  onClick 
}: RoundTabProps) => {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.button
            whileHover={!isLocked ? { y: -1 } : {}}
            whileTap={!isLocked ? { scale: 0.97 } : {}}
            onClick={onClick}
            className={`
              relative flex flex-col items-center gap-1 px-5 py-3
              rounded-xl border transition-all duration-300
              ${isLocked ? "cursor-not-allowed select-none" : "cursor-pointer"}
            `}
            style={{
              opacity: isLocked ? 0.3 : isActive ? 1 : 0.7,
              filter: isLocked ? "grayscale(80%)" : "none",
              background: isActive
                ? "rgba(99, 102, 241, 0.15)"
                : isCompleted
                ? "rgba(34, 197, 94, 0.06)"
                : "rgba(255,255,255,0.03)",
              borderColor: isActive
                ? "rgba(99, 102, 241, 0.5)"
                : isCompleted
                ? "rgba(34, 197, 94, 0.25)"
                : "rgba(255,255,255,0.08)",
              boxShadow: isActive
                ? "0 0 20px rgba(99, 102, 241, 0.2)"
                : "none",
            }}
          >
            {/* ROUND NUMBER BADGE */}
            <div className="flex items-center gap-1.5">
              {isCompleted ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : isLocked ? (
                <Lock className="w-3.5 h-3.5 text-white/30" />
              ) : (
                <IconComponent
                  className="w-4 h-4"
                  style={{ color: isActive ? "#818cf8" : "rgba(255,255,255,0.5)" }}
                />
              )}
              <span
                className="text-[13px] font-bold tracking-tight"
                style={{
                  fontFamily: "'Poppins', sans-serif",
                  color: isActive
                    ? "#c7d2fe"
                    : isCompleted
                    ? "#6ee7b7"
                    : "rgba(255,255,255,0.5)"
                }}
              >
                {label}
              </span>
            </div>
            <span
              className="text-[9px] uppercase tracking-widest font-medium"
              style={{
                color: isActive
                  ? "rgba(165,180,252,0.8)"
                  : "rgba(255,255,255,0.25)"
              }}
            >
              {sublabel}
            </span>

            {/* ACTIVE INDICATOR DOT */}
            {isActive && (
              <motion.div
                className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 
                           w-1 h-1 rounded-full bg-indigo-400"
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </motion.button>
        </TooltipTrigger>
        {isLocked && (
          <TooltipContent side="bottom" className="
            bg-gray-900/95 border border-white/10 
            text-white/80 text-[11px] px-3 py-1.5
          ">
            🔒 Complete Round {number - 1} first
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  )
}

export default RoundTab
