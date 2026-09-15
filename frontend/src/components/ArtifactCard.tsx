import React from 'react';
import { FileText, Code2, ArrowUpRight, CheckSquare, Compass, Beaker, Layout, BookOpen } from 'lucide-react';
import { Artifact } from '../types/api';

interface ArtifactCardProps {
  artifact: Artifact;
  onOpenViewer: (artifact: Artifact) => void;
}

export const ArtifactCard: React.FC<ArtifactCardProps> = ({ artifact, onOpenViewer }) => {
  const getIcon = () => {
    switch (artifact.artifact_type) {
      case 'growth_action_plan':
        return <Layout className="w-4 h-4 text-blue-600" />;
      case 'ship30_essay':
        return <BookOpen className="w-4 h-4 text-blue-600" />;
      case 'framework':
        return <Compass className="w-4 h-4 text-emerald-600" />;
      case 'checklist':
        return <CheckSquare className="w-4 h-4 text-violet-600" />;
      case 'experiment_plan':
        return <Beaker className="w-4 h-4 text-rose-500" />;
      case 'strategy_doc':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'html_css_component':
        return <Code2 className="w-4 h-4 text-blue-600" />;
      default:
        return <FileText className="w-4 h-4 text-blue-600" />;
    }
  };

  const getTypeName = () => {
    switch (artifact.artifact_type) {
      case 'growth_action_plan':
        return 'Growth Action Plan';
      case 'ship30_essay':
        return 'Ship 30 Essay';
      case 'framework':
        return 'Growth Framework';
      case 'checklist':
        return 'Audit Checklist';
      case 'experiment_plan':
        return 'Experiment Plan';
      case 'strategy_doc':
        return 'Strategy Document';
      case 'html_css_component':
        return 'HTML/CSS Component';
      default:
        return artifact.artifact_type;
    }
  };

  const wordCount =
    artifact.artifact_metadata?.word_count ||
    artifact.content.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="mt-3 p-4 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1 transition-all duration-300 shadow-xs group">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3 min-w-0 flex-1 mr-3">
          <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0 shadow-2xs group-hover:scale-110 transition-transform duration-200">
            {getIcon()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-blue-600">
                {getTypeName()}
              </span>
              <span className="px-1.5 py-0.2 rounded text-[9px] bg-slate-100 border border-slate-200 text-slate-500 uppercase font-mono">
                {artifact.content_format}
              </span>
              <span className="text-[10px] text-slate-400">
                {wordCount} words
              </span>
            </div>
            <h4 className="text-xs md:text-sm font-bold text-slate-900 truncate mt-0.5 group-hover:text-blue-600 transition-colors">
              {artifact.title}
            </h4>
          </div>
        </div>

        <button
          onClick={() => onOpenViewer(artifact)}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-600 text-blue-600 hover:text-white border border-blue-200 hover:border-blue-600 text-xs font-semibold transition-all shadow-2xs active:scale-95"
        >
          <span>Open Artifact</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
