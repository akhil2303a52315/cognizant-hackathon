interface ModelBadgeProps {
  model: string
  modelProvider: string
  modelColor: string
  modelIcon: string
}

const ModelBadge = ({ model, modelProvider, modelColor, modelIcon }: ModelBadgeProps) => (
  <div className="flex items-center gap-1.5 mt-2">
    <span className="text-xs">{modelIcon}</span>
    <span
      className="
        text-[10px] font-semibold tracking-wide px-2.5 py-0.5
        rounded-full border backdrop-blur-sm
      "
      style={{
        color: modelColor,
        borderColor: `${modelColor}40`,
        backgroundColor: `${modelColor}15`,
      }}
    >
      {model}
    </span>
    <span className="text-[9px] text-white/30 font-medium">
      via {modelProvider}
    </span>
  </div>
)

export default ModelBadge
