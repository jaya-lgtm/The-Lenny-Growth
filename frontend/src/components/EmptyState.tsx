import React, { useState, useMemo } from 'react';
import { Users, Target, FlaskConical, ArrowRight, Sprout, Plus, Quote, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  onStartNewChat: () => void;
  isChatBoxVisible?: boolean;
}

const PROMPT_SUGGESTIONS = [
  {
    title: 'Activation & Onboarding',
    prompt: 'How do I improve user activation?',
    icon: Users,
    badge: 'FRAMEWORK',
  },
  {
    title: 'Retention & Churn',
    prompt: 'What are effective retention strategies?',
    icon: Target,
    badge: 'STRATEGY',
  },
  {
    title: 'Experimentation',
    prompt: 'How should I prioritize growth experiments?',
    icon: FlaskConical,
    badge: 'EXECUTION',
  },
];

const PRODUCT_GROWTH_QUOTES = [
  {
    quote: "Retention is the king of growth. If your product doesn't retain users, everything else is just pouring water into a leaky bucket.",
    author: "Lenny Rachitsky",
    role: "Lenny's Podcast & Newsletter",
  },
  {
    quote: "The fastest way to grow is to make something people genuinely love and enthusiastically tell their friends about.",
    author: "Paul Graham",
    role: "Y Combinator",
  },
  {
    quote: "Fall in love with the problem your user has, not your first solution.",
    author: "Shreyas Doshi",
    role: "Product Leader (ex-Stripe, Twitter)",
  },
  {
    quote: "Growth is not a bag of hacks. It's a scientific process of rapid experimentation and disciplined learning.",
    author: "Brian Balfour",
    role: "Founder & CEO, Reforge",
  },
  {
    quote: "Product-led growth isn't about removing human touch; it's about removing friction from the user's moment of value.",
    author: "Elena Verna",
    role: "Head of Growth, Dropbox & Amplitude",
  },
  {
    quote: "Do things that don't scale until you find product-market fit.",
    author: "Paul Graham",
    role: "Founder, Y Combinator",
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({
  onSelectPrompt,
  onStartNewChat,
  isChatBoxVisible = false,
}) => {
  const [quoteIndex, setQuoteIndex] = useState(() =>
    Math.floor(Math.random() * PRODUCT_GROWTH_QUOTES.length)
  );
  const currentQuote = useMemo(() => PRODUCT_GROWTH_QUOTES[quoteIndex], [quoteIndex]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-4xl mx-auto text-center select-none animate-fade-in-up">
      {/* Center Sprout Icon */}
      <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-xs transition-transform duration-300 hover:scale-105">
        <Sprout className="w-7 h-7 animate-pulse-glow" />
      </div>

      {/* Clean Quotation Card - Always centered and present */}
      <div
        onClick={() => setQuoteIndex((prev) => (prev + 1) % PRODUCT_GROWTH_QUOTES.length)}
        className="my-3 w-full max-w-xl mx-auto px-7 py-5 rounded-2xl bg-gradient-to-r from-blue-50/80 via-slate-50 to-blue-50/80 border border-blue-100 shadow-2xs cursor-pointer hover:border-blue-300 hover:shadow-xs transition-all group"
        title="Click to view another quote"
      >
        <div className="flex items-center justify-center space-x-1.5 text-xs font-semibold text-blue-600 mb-2">
          <Quote className="w-4 h-4 text-blue-500 fill-blue-100" />
          <span>Product Wisdom</span>
          <Sparkles className="w-3.5 h-3.5 text-blue-400 group-hover:rotate-12 transition-transform" />
        </div>
        <p className="text-sm md:text-base italic text-slate-800 leading-relaxed font-serif">
          "{currentQuote.quote}"
        </p>
        <cite className="block mt-2 text-xs font-semibold text-blue-600 not-italic">
          — {currentQuote.author}, <span className="text-slate-500 font-normal">{currentQuote.role}</span>
        </cite>
      </div>

      {/* Suggestion Cards & Start New Chat Button - Present initially, disappears on Start New Chat */}
      <div
        className={`w-full transition-all duration-500 ease-in-out transform ${
          !isChatBoxVisible
            ? 'opacity-100 translate-y-0 max-h-[600px] mt-4 pointer-events-auto'
            : 'opacity-0 -translate-y-4 max-h-0 mt-0 pointer-events-none overflow-hidden'
        }`}
      >
        {/* 3 Suggestion Cards */}
        <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 text-left">
          {PROMPT_SUGGESTIONS.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                type="button"
                onClick={() => onSelectPrompt(item.prompt)}
                className="group p-5 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1 active:scale-[0.98] transition-all duration-300 flex flex-col justify-between shadow-2xs cursor-pointer"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 border border-blue-100/80 flex items-center justify-center group-hover:scale-110 transition-transform duration-200">
                      <Icon className="w-4 h-4" />
                    </span>
                    <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                      {item.badge}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors mb-1.5">
                    {item.title}
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    "{item.prompt}"
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-xs font-semibold text-blue-600 group-hover:text-blue-700">
                  <span>Ask this</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1.5 group-hover:translate-x-1 transition-transform duration-200" />
                </div>
              </button>
            );
          })}
        </div>

        {/* Start New Chat Action Button */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            type="button"
            onClick={onStartNewChat}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white text-sm font-semibold shadow-md shadow-blue-500/25 hover:shadow-lg transition-all cursor-pointer group"
          >
            <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
            <span>Start New Chat</span>
          </button>
        </div>
      </div>

      {/* Subtle Grounding Footnote */}
      <div className="mt-7 text-[11px] text-slate-400 flex items-center space-x-2 font-medium">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
        </span>
        <span>Grounded across 272+ Lenny's Podcast episodes with 37,200+ transcript chunks in PostgreSQL pgvector</span>
      </div>
    </div>
  );
};
