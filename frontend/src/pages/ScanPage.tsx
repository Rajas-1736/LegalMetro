import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import { ScanJobResult, ScanJobStatus } from '../types';
import { StageProgressBar } from '../components/scanner/StageProgressBar';
import { AnnotatedImageViewer } from '../components/scanner/AnnotatedImageViewer';
import { RuleChecklistPanel } from '../components/scanner/RuleChecklistPanel';
import { 
  UploadCloud, FileImage, Ruler, CheckCircle, AlertTriangle, 
  Sparkles, RefreshCcw, ArrowRight, ShieldCheck, HelpCircle,
  Plus, Trash2, ArrowUp, ArrowDown, QrCode, Calculator, Scale,
  CheckCircle2, XCircle, Upload, ExternalLink, Copy, Check,
  Camera, SwitchCamera, VideoOff
} from 'lucide-react';

interface ScanPageProps {
  onViewReport: (scanId: string) => void;
}

interface PanelItem {
  id: string;
  file: File;
  previewUrl: string;
  name: string;
}

export const ScanPage: React.FC<ScanPageProps> = ({ onViewReport }) => {
  const { t } = useTranslation();
  const [panels, setPanels] = useState<PanelItem[]>([]);
  const [activePanelIndex, setActivePanelIndex] = useState<number>(0);
  const [referenceScaleMm, setReferenceScaleMm] = useState<string>('85');
  const [productName, setProductName] = useState<string>('');
  const [category, setCategory] = useState<string>('Packaged Food');
  const [inspectorNotes, setInspectorNotes] = useState<string>('');

  // Scanning State
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ScanJobStatus | null>(null);
  const [scanResult, setScanResult] = useState<ScanJobResult | null>(null);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [qrScreenshot, setQrScreenshot] = useState<File | null>(null);
  const [isUploadingQr, setIsUploadingQr] = useState<boolean>(false);
  const [isSkippingQr, setIsSkippingQr] = useState<boolean>(false);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [selectedQrIndex, setSelectedQrIndex] = useState<number>(0);
  const [customPortalUrl, setCustomPortalUrl] = useState<string>('');
  const [isEditingUrl, setIsEditingUrl] = useState<boolean>(false);
  const [batchCodePresence, setBatchCodePresence] = useState<'present' | 'absent'>('present');
  const [editableBatchCode, setEditableBatchCode] = useState<string>('');
  const [isSubmittingNoBatchCode, setIsSubmittingNoBatchCode] = useState<boolean>(false);
  const hasAutoOpenedQr = useRef<boolean>(false);

  // Camera & Capture State
  const [uploadMode, setUploadMode] = useState<'file' | 'camera'>('file');
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [isCameraLoading, setIsCameraLoading] = useState<boolean>(false);
  const [cameraFacingMode, setCameraFacingMode] = useState<'environment' | 'user'>('environment');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isFlashing, setIsFlashing] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const qrFileInputRef = useRef<HTMLInputElement>(null);
  const mobileCameraInputRef = useRef<HTMLInputElement>(null);
  const mobileQrCameraInputRef = useRef<HTMLInputElement>(null);

  const handleUploadQrEvidence = async () => {
    const targetJobId = jobId || scanResult?.id;
    if (!qrScreenshot || !targetJobId) return;
    setIsUploadingQr(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('qr_screenshot', qrScreenshot);
      const codeToSubmit = editableBatchCode.trim() || (jobStatus?.code_to_enter || '').trim();
      if (codeToSubmit) {
        fd.append('batch_code', codeToSubmit);
      }
      await api.products.submitQrEvidence(targetJobId, fd);
      setQrScreenshot(null);
      setIsScanning(true);
      setJobId(targetJobId);
      setScanResult(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit QR portal screenshot evidence.');
    } finally {
      setIsUploadingQr(false);
    }
  };

  const handleConfirmNoBatchCode = async () => {
    const targetJobId = jobId || scanResult?.id;
    if (!targetJobId) return;
    setIsSubmittingNoBatchCode(true);
    setError(null);
    try {
      await api.products.submitNoBatchCode(targetJobId);
      setIsScanning(true);
      setJobId(targetJobId);
      setScanResult(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record absence of batch code.');
    } finally {
      setIsSubmittingNoBatchCode(false);
    }
  };

  const handleSkipQrVerification = async () => {
    const targetJobId = jobId || scanResult?.id;
    if (!targetJobId) return;
    setIsSkippingQr(true);
    setError(null);
    try {
      await api.products.skipQrEvidence(targetJobId);
      setIsScanning(true);
      setJobId(targetJobId);
      setScanResult(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to skip QR portal verification.');
    } finally {
      setIsSkippingQr(false);
    }
  };

  // Polling for scan progress
  useEffect(() => {
    let interval: any = null;
    if (jobId && isScanning) {
      interval = setInterval(async () => {
        try {
          const status = await api.products.getScanStatus(jobId);
          setJobStatus(status);

          // Auto-open portal website in new tab once when entering AWAITING_QR_EVIDENCE
          if (status.status === 'AWAITING_QR_EVIDENCE' && status.detected_qr_url && !hasAutoOpenedQr.current) {
            hasAutoOpenedQr.current = true;
            try {
              window.open(status.detected_qr_url, '_blank', 'noopener,noreferrer');
            } catch (popupErr) {
              console.warn('Auto-opening QR portal popup was blocked by browser', popupErr);
            }
          }

          if (status.status === 'COMPLETED') {
            setIsScanning(false);
            clearInterval(interval);
            const result = await api.products.getScanResult(jobId);
            setScanResult(result);
            setActivePanelIndex(0);
          } else if (status.status === 'FAILED') {
            setIsScanning(false);
            clearInterval(interval);
            setError(status.current_stage_message || 'Pipeline execution failed.');
          }
        } catch (err: any) {
          console.error('Polling error', err);
        }
      }, 750);
    }
    return () => clearInterval(interval);
  }, [jobId, isScanning]);

  useEffect(() => {
    if (jobStatus?.code_to_enter && !editableBatchCode) {
      setEditableBatchCode(jobStatus.code_to_enter);
    }
  }, [jobStatus?.code_to_enter]);

  const startCamera = async (facing: 'environment' | 'user' = cameraFacingMode) => {
    setIsCameraLoading(true);
    setCameraError(null);
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        // Mobile or non-HTTPS environment: trigger native phone camera directly
        if (mobileCameraInputRef.current) {
          setIsCameraLoading(false);
          mobileCameraInputRef.current.click();
          return;
        }
        throw new Error('Camera access is not supported in this browser environment or requires HTTPS/localhost.');
      }

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: facing },
            width: { ideal: 1920, min: 1024 },
            height: { ideal: 1080, min: 720 },
          },
          audio: false,
        });
      } catch (e) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: facing },
          audio: false,
        });
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch((playErr) => console.warn('Video playback warning:', playErr));
      }
      setCameraActive(true);
    } catch (err: any) {
      console.error('Camera access error:', err);
      let message = 'Unable to access device camera.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        message = 'Camera permission was denied. Please allow camera permissions in your browser address bar and reload.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        message = 'No camera device was detected on your hardware.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        message = 'Camera is already in use by another application or tab.';
      } else if (err.message) {
        message = err.message;
      }
      setCameraError(message);
      setCameraActive(false);
    } finally {
      setIsCameraLoading(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const switchCameraFacing = async () => {
    const nextFacing = cameraFacingMode === 'environment' ? 'user' : 'environment';
    setCameraFacingMode(nextFacing);
    if (uploadMode === 'camera') {
      await startCamera(nextFacing);
    }
  };

  const handleSwitchMode = (mode: 'file' | 'camera') => {
    if (mode === 'camera' && (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)) {
      if (mobileCameraInputRef.current) {
        mobileCameraInputRef.current.click();
        return;
      }
    }
    setUploadMode(mode);
    if (mode === 'camera') {
      startCamera(cameraFacingMode);
    } else {
      stopCamera();
    }
  };

  const handleTriggerMobileCamera = () => {
    if (mobileCameraInputRef.current) {
      mobileCameraInputRef.current.click();
    } else {
      handleSwitchMode('camera');
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    if (!video) return;

    const w = video.videoWidth || 1280;
    const h = video.videoHeight || 720;
    if (w === 0 || h === 0) return;

    setIsFlashing(true);
    setTimeout(() => setIsFlashing(false), 200);

    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, w, h);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const panelNum = panels.length + 1;
        const timeStr = new Date().toISOString().slice(11, 19).replace(/:/g, '');
        const filename = `Panel_${panelNum}_Camera_${timeStr}.jpg`;
        const file = new File([blob], filename, { type: 'image/jpeg' });
        addFilesToPanels([file]);
      },
      'image/jpeg',
      0.95
    );
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const addFilesToPanels = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    if (fileArray.length === 0) return;

    const newItems: PanelItem[] = fileArray.map((file) => ({
      id: Math.random().toString(36).substring(2, 9),
      file,
      previewUrl: URL.createObjectURL(file),
      name: file.name,
    }));

    setPanels((prev) => {
      const combined = [...prev, ...newItems];
      if (!productName && combined.length > 0) {
        const firstName = combined[0].name;
        if (firstName.includes('Camera')) {
          setProductName('Field Inspection Sample');
        } else {
          setProductName(firstName.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' '));
        }
      }
      return combined;
    });
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToPanels(e.target.files);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleMobileCameraCapture = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToPanels(e.target.files);
    }
    if (e.target) {
      e.target.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToPanels(e.dataTransfer.files);
    }
  };

  const removePanel = (id: string) => {
    setPanels((prev) => prev.filter((p) => p.id !== id));
  };

  const movePanel = (index: number, direction: 'up' | 'down') => {
    setPanels((prev) => {
      const copy = [...prev];
      const targetIndex = direction === 'up' ? index - 1 : index + 1;
      if (targetIndex < 0 || targetIndex >= copy.length) return prev;
      const temp = copy[index];
      copy[index] = copy[targetIndex];
      copy[targetIndex] = temp;
      return copy;
    });
  };

  const startScan = async () => {
    if (panels.length === 0) {
      setError('Please upload or capture at least one packaging panel image.');
      return;
    }

    stopCamera();
    setIsScanning(true);
    setError(null);
    setScanResult(null);
    hasAutoOpenedQr.current = false;

    const formData = new FormData();
    panels.forEach((p) => {
      formData.append('images', p.file);
    });
    // Fallback for single-image endpoints
    formData.append('image', panels[0].file);
    if (panels.length > 1) {
      formData.append('back_image', panels[1].file);
    }
    if (referenceScaleMm && !isNaN(Number(referenceScaleMm))) {
      formData.append('reference_scale_mm', referenceScaleMm);
    }
    if (productName) formData.append('product_name', productName);
    if (category) formData.append('category', category);
    if (inspectorNotes) formData.append('inspector_notes', inspectorNotes);

    try {
      const data = await api.products.scan(formData);
      setJobId(data.job_id);
    } catch (err: any) {
      setIsScanning(false);
      setError(err.response?.data?.detail || 'Failed to initiate scanning pipeline');
    }
  };

  const resetScan = () => {
    stopCamera();
    setUploadMode('file');
    setPanels([]);
    setActivePanelIndex(0);
    setJobId(null);
    setJobStatus(null);
    setScanResult(null);
    setIsScanning(false);
    setError(null);
    setSelectedRuleId(null);
    hasAutoOpenedQr.current = false;
    setBatchCodePresence('present');
    setEditableBatchCode('');
    setIsSubmittingNoBatchCode(false);
  };

  const handleSelectRule = (ruleId: string | null) => {
    setSelectedRuleId(ruleId);
    if (ruleId && scanResult) {
      const foundRule = scanResult.rule_results.find((r) => r.rule_id === ruleId);
      if (foundRule && foundRule.image_index !== undefined) {
        setActivePanelIndex(foundRule.image_index);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      
      {/* Page Title & SIH Callout */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <span>{t('scan.title')}</span>
            <span className="text-xs bg-blue-100 text-blue-800 font-mono px-2 py-0.5 rounded-full font-bold">
              Gemini Multimodal + 2011 Rules
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {t('scan.subtitle')}
          </p>
        </div>

        {scanResult && (
          <button
            onClick={resetScan}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold self-start cursor-pointer"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
            <span>Scan Another Package</span>
          </button>
        )}
      </div>

      {error && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 text-xs ${
          error.toLowerCase().includes('quota') || error.toLowerCase().includes('gemini') || error.toLowerCase().includes('rate limit')
            ? 'bg-amber-50 border-amber-300 text-amber-900 shadow-sm'
            : 'bg-rose-50 border-rose-300 text-rose-800'
        }`}>
          <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${
            error.toLowerCase().includes('quota') ? 'text-amber-600' : 'text-rose-600'
          }`} />
          <div className="space-y-1">
            <div className="font-bold text-sm">
              {error.toLowerCase().includes('quota') ? 'Google AI Studio Scan Quota Exceeded' : 'Inspection Pipeline Error'}
            </div>
            <div className="leading-relaxed">{error}</div>
            {error.toLowerCase().includes('quota') && (
              <div className="text-[11px] text-amber-800 pt-1.5 border-t border-amber-200 mt-2">
                💡 <strong>Quick Fix:</strong> The Gemini model has a free-tier limit. To resume immediately:
                1) Open <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" className="underline font-bold hover:text-amber-950">Google AI Studio</a>.
                2) Click <em>Create API Key</em> in a new project.
                3) Update <code>GEMINI_API_KEY</code> in your root <code>.env</code> file.
              </div>
            )}
          </div>
        </div>
      )}

      {/* VIEW 1: UPLOAD & SETUP STATE */}
      {!scanResult && !isScanning && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Upload Zone */}
          <div className="lg:col-span-2 space-y-4">
            {/* Mode Switcher Tabs: Upload Files vs Live Camera */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
              <button
                type="button"
                onClick={() => handleSwitchMode('file')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-xs font-bold transition cursor-pointer ${
                  uploadMode === 'file'
                    ? 'bg-white text-slate-800 shadow-sm border border-slate-200/60'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <UploadCloud className="w-4 h-4 text-blue-600" />
                <span>{t('scan.tab_files')}</span>
                {panels.length > 0 && uploadMode !== 'file' && (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-200 text-slate-700 font-mono">
                    {panels.length}
                  </span>
                )}
              </button>
              <button
                type="button"
                onClick={() => handleSwitchMode('camera')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-xs font-bold transition cursor-pointer ${
                  uploadMode === 'camera'
                    ? 'bg-white text-blue-700 shadow-sm border border-slate-200/60'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <Camera className="w-4 h-4 text-blue-600" />
                <span>{t('scan.tab_camera')}</span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                  Field Inspection
                </span>
                {panels.length > 0 && uploadMode === 'camera' && (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-blue-100 text-blue-700 font-mono">
                    {t('scan.camera_captured_count', { count: panels.length })}
                  </span>
                )}
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />
            {/* Native Mobile Camera Input: Bypasses HTTP/SSL limitations on mobile */}
            <input
              ref={mobileCameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleMobileCameraCapture}
              className="hidden"
            />
            {/* Native Mobile QR Camera Input */}
            <input
              ref={mobileQrCameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setQrScreenshot(e.target.files[0]);
                }
                if (e.target) e.target.value = '';
              }}
              className="hidden"
            />

            {uploadMode === 'camera' ? (
              <div className="space-y-4">
                {/* Viewfinder Container */}
                {cameraError ? (
                  <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center space-y-3">
                    <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
                      <VideoOff className="w-6 h-6" />
                    </div>
                    <div className="max-w-md mx-auto">
                      <h4 className="text-sm font-bold text-rose-900">Camera Access Issue</h4>
                      <p className="text-xs text-rose-700 mt-1 leading-relaxed">{cameraError}</p>
                      <p className="text-[11px] text-slate-600 mt-2 bg-white/80 p-2.5 rounded-lg border border-rose-200 text-left">
                        <strong className="text-slate-800">Field Tip:</strong> Mobile browsers restrict WebRTC video streams over plain HTTP, but you can capture high-resolution packaging photos directly using your smartphone's native camera below:
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                      <button
                        type="button"
                        onClick={handleTriggerMobileCamera}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                      >
                        <Camera className="w-4 h-4" />
                        <span>Take Photo with Phone Camera</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => startCamera(cameraFacingMode)}
                        className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition cursor-pointer"
                      >
                        Retry Web Camera
                      </button>
                      <button
                        type="button"
                        onClick={() => handleSwitchMode('file')}
                        className="px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition cursor-pointer"
                      >
                        Switch to File Upload
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="relative bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-xl min-h-[380px] flex items-center justify-center">
                    {/* Live Video Feed */}
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-auto max-h-[440px] object-cover"
                    />

                    {/* Snapshot Flash Overlay */}
                    {isFlashing && (
                      <div className="absolute inset-0 bg-white z-30 pointer-events-none transition-opacity duration-200" />
                    )}

                    {/* Viewfinder Reticle & HUD Overlay */}
                    <div className="absolute inset-0 pointer-events-none p-4 sm:p-5 flex flex-col justify-between">
                      {/* Top Bar HUD */}
                      <div className="flex items-center justify-between pointer-events-auto">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/60 backdrop-blur-md text-[11px] font-bold text-white border border-white/20">
                            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                            LIVE CAMERA
                          </span>
                          <span className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-[11px] font-medium text-slate-200 border border-white/20">
                            Panel {panels.length + 1}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={switchCameraFacing}
                            title={`Switch to ${cameraFacingMode === 'environment' ? 'Front' : 'Rear'} Camera`}
                            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md text-[11px] font-semibold text-white border border-white/20 transition"
                          >
                            <SwitchCamera className="w-3.5 h-3.5" />
                            <span>{cameraFacingMode === 'environment' ? 'Rear Cam' : 'Front Cam'}</span>
                          </button>
                        </div>
                      </div>

                      {/* Center Framing Brackets / Guide */}
                      <div className="relative my-auto w-full max-w-md mx-auto aspect-[4/3] max-h-[220px] pointer-events-none">
                        <div className="absolute top-0 left-0 w-7 h-7 border-t-2 border-l-2 border-emerald-400 rounded-tl-lg shadow-sm" />
                        <div className="absolute top-0 right-0 w-7 h-7 border-t-2 border-r-2 border-emerald-400 rounded-tr-lg shadow-sm" />
                        <div className="absolute bottom-0 left-0 w-7 h-7 border-b-2 border-l-2 border-emerald-400 rounded-bl-lg shadow-sm" />
                        <div className="absolute bottom-0 right-0 w-7 h-7 border-b-2 border-r-2 border-emerald-400 rounded-br-lg shadow-sm" />

                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-[11px] font-semibold text-white/90 bg-black/50 backdrop-blur-sm px-3 py-1 rounded-full border border-white/10">
                            Align packaging label within brackets
                          </span>
                        </div>
                      </div>

                      {/* Bottom Shutter Trigger Bar */}
                      <div className="flex flex-col items-center justify-center pointer-events-auto pb-1">
                        <button
                          type="button"
                          onClick={capturePhoto}
                          disabled={!cameraActive || isCameraLoading}
                          className="group relative flex items-center justify-center p-1 rounded-full transition active:scale-95 disabled:opacity-50"
                          title="Snap Photo (Adds as Next Packaging Panel)"
                        >
                          <div className="w-16 h-16 rounded-full border-4 border-white group-hover:border-emerald-400 transition-colors flex items-center justify-center shadow-lg bg-black/30 backdrop-blur-sm">
                            <div className="w-11 h-11 rounded-full bg-white group-hover:bg-emerald-400 transition-colors flex items-center justify-center text-slate-900">
                              <Camera className="w-5 h-5 text-slate-800" />
                            </div>
                          </div>
                        </button>
                        <span className="text-[10px] text-white/80 font-medium drop-shadow mt-1">
                          Tap to capture Panel {panels.length + 1}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Captured Panels Review Strip in Camera Mode */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b pb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Packaging Panels ({panels.length} Captured)
                      </span>
                      {panels.length > 0 && (
                        <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full">
                          Ready to Inspect
                        </span>
                      )}
                    </div>
                    {panels.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setPanels([])}
                        className="px-2 py-1 text-xs text-slate-400 hover:text-rose-600 rounded transition"
                      >
                        Clear All
                      </button>
                    )}
                  </div>

                  {panels.length === 0 ? (
                    <div className="py-6 text-center text-slate-400 text-xs flex flex-col items-center justify-center space-y-1">
                      <Camera className="w-8 h-8 text-slate-300 stroke-[1.5]" />
                      <p className="font-medium text-slate-600">No photos captured yet</p>
                      <p className="text-[11px] text-slate-400">Position the package front, back, or sides and click the shutter button above.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1">
                      {panels.map((panel, idx) => (
                        <div
                          key={panel.id}
                          className="border border-slate-200 rounded-lg p-2 bg-slate-50 flex flex-col justify-between space-y-2 group hover:border-blue-300 transition"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                              Panel {idx + 1}
                            </span>
                            <div className="flex items-center space-x-1">
                              {idx > 0 && (
                                <button
                                  type="button"
                                  onClick={() => movePanel(idx, 'up')}
                                  title="Move left/up"
                                  className="p-0.5 hover:bg-slate-200 rounded text-slate-500"
                                >
                                  <ArrowUp className="w-3 h-3" />
                                </button>
                              )}
                              {idx < panels.length - 1 && (
                                <button
                                  type="button"
                                  onClick={() => movePanel(idx, 'down')}
                                  title="Move right/down"
                                  className="p-0.5 hover:bg-slate-200 rounded text-slate-500"
                                >
                                  <ArrowDown className="w-3 h-3" />
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => removePanel(panel.id)}
                                title="Remove / Retake panel"
                                className="p-0.5 hover:bg-rose-100 text-slate-400 hover:text-rose-600 rounded"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>

                          <div className="h-32 bg-white rounded border border-slate-200 overflow-hidden flex items-center justify-center p-1">
                            <img
                              src={panel.previewUrl}
                              alt={panel.name}
                              className="max-h-full max-w-full object-contain"
                            />
                          </div>

                          <div className="text-[10px] text-slate-600 font-mono truncate" title={panel.name}>
                            {panel.name}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* File Upload Mode */
              panels.length === 0 ? (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-300 hover:border-blue-400 bg-white hover:bg-slate-50/60 rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center min-h-[320px]"
                >
                  <div className="space-y-3 max-w-sm">
                    <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
                      <UploadCloud className="w-7 h-7" />
                    </div>
                    <div>
                      <span className="text-sm font-bold text-slate-800 block">
                        Upload Packaged Product Label Panels
                      </span>
                      <span className="text-xs text-slate-500">
                        Drag & drop 1 or more panels (Front, Back, Side, Base) or click to browse
                      </span>
                    </div>
                    <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2">
                      <span className="inline-block px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-[11px] font-semibold border border-blue-100">
                        Multi-Panel Clustered Extraction
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTriggerMobileCamera();
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-full text-[11px] font-semibold border border-emerald-200 transition cursor-pointer"
                      >
                        <Camera className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Take Photo / Live Camera</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        Packaging Panels ({panels.length} Uploaded)
                      </span>
                      <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                        Reorder panels or add more
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={handleTriggerMobileCamera}
                        className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 rounded-md transition border border-emerald-200 cursor-pointer"
                      >
                        <Camera className="w-3.5 h-3.5" />
                        <span>Take Photo</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md transition"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add Another Panel</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setPanels([])}
                        className="px-2 py-1 text-xs text-slate-400 hover:text-rose-600 rounded transition"
                      >
                        Clear All
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1">
                    {panels.map((panel, idx) => (
                      <div
                        key={panel.id}
                        className="border border-slate-200 rounded-lg p-2 bg-slate-50 flex flex-col justify-between space-y-2 group hover:border-blue-300 transition"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-800">
                            Panel {idx + 1}
                          </span>
                          <div className="flex items-center space-x-1">
                            {idx > 0 && (
                              <button
                                type="button"
                                onClick={() => movePanel(idx, 'up')}
                                title="Move left/up"
                                className="p-0.5 hover:bg-slate-200 rounded text-slate-500"
                              >
                                <ArrowUp className="w-3 h-3" />
                              </button>
                            )}
                            {idx < panels.length - 1 && (
                              <button
                                type="button"
                                onClick={() => movePanel(idx, 'down')}
                                title="Move right/down"
                                className="p-0.5 hover:bg-slate-200 rounded text-slate-500"
                              >
                                <ArrowDown className="w-3 h-3" />
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => removePanel(panel.id)}
                              title="Remove panel"
                              className="p-0.5 hover:bg-rose-100 text-slate-400 hover:text-rose-600 rounded"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>

                        <div className="h-32 bg-white rounded border border-slate-200 overflow-hidden flex items-center justify-center p-1">
                          <img
                            src={panel.previewUrl}
                            alt={panel.name}
                            className="max-h-full max-w-full object-contain"
                          />
                        </div>

                        <div className="text-[10px] text-slate-600 font-mono truncate" title={panel.name}>
                          {panel.name}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}
          </div>

          {/* Inspection Metadata & Scale Controls */}
          <div className="space-y-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b pb-2">
                Inspection Parameters
              </h3>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('scan.prod_name_label')}
                </label>
                <input
                  type="text"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder={t('scan.prod_name_placeholder')}
                  className="w-full text-xs px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('scan.cat_label')}
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full text-xs px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                >
                  <option>Packaged Food</option>
                  <option>Beverages & Oils</option>
                  <option>Cosmetics & Toiletries</option>
                  <option>Household Chemicals</option>
                  <option>Imported Goods</option>
                  <option>Consumer Electronics</option>
                </select>
              </div>

              {/* Physical Scale Reference Input */}
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-800 flex items-center gap-1">
                    <Ruler className="w-3.5 h-3.5 text-blue-600" />
                    <span>{t('scan.scale_label')}</span>
                  </label>
                  <span className="text-[10px] text-slate-400 font-mono">Rule 7 / Sched II</span>
                </div>
                <input
                  type="number"
                  value={referenceScaleMm}
                  onChange={(e) => setReferenceScaleMm(e.target.value)}
                  placeholder={t('scan.scale_placeholder')}
                  className="w-full text-xs px-3 py-1.5 border rounded bg-white focus:ring-2 focus:ring-blue-500 outline-none font-mono"
                />
                <p className="text-[10px] text-slate-500 leading-tight">
                  {t('scan.scale_hint')}
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t('scan.notes_label')}
                </label>
                <textarea
                  rows={2}
                  value={inspectorNotes}
                  onChange={(e) => setInspectorNotes(e.target.value)}
                  placeholder={t('scan.notes_placeholder')}
                  className="w-full text-xs px-3 py-1.5 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <button
                type="button"
                onClick={startScan}
                disabled={panels.length === 0}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-bold text-xs shadow-md transition flex items-center justify-center space-x-2 cursor-pointer"
              >
                <span>{t('scan.btn_start_scan')}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

        </div>
      )}

      {/* VIEW 2: LIVE SCANNING PROGRESS OR ATTENDED QR VERIFICATION */}
      {isScanning && jobStatus && (
        <div className="max-w-2xl mx-auto py-8">
          {jobStatus.status === 'AWAITING_QR_EVIDENCE' ? (
            <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-md border-2 border-indigo-200 space-y-6 animate-in fade-in duration-300">
              {/* Header Badge & Title */}
              <div className="flex items-start space-x-4 border-b border-slate-100 pb-5">
                <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 shadow-inner">
                  <QrCode className="w-7 h-7" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-900 border border-amber-200">
                      Action Required • Rule 6(1)(a)
                    </span>
                    <span className="text-xs text-slate-400 font-mono">Job ID: {jobStatus.id.slice(0, 8)}</span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 leading-tight">
                    {t('scan.qr_card_title')}
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {t('scan.qr_card_desc')}
                  </p>
                </div>
              </div>

              {/* Action Steps */}
              <div className="space-y-4">
                {/* Multi-QR Candidate Selector (Rendered if >1 compliance QRs detected) */}
                {jobStatus.available_compliance_qrs && jobStatus.available_compliance_qrs.length > 1 && (
                  <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
                        <QrCode className="w-4 h-4 text-amber-700" />
                        <span>Multiple Compliance QRs Found ({jobStatus.available_compliance_qrs.length})</span>
                      </span>
                      <span className="text-[10px] text-amber-800 font-medium">Select QR code to verify</span>
                    </div>
                    <div className="space-y-2">
                      {jobStatus.available_compliance_qrs.map((qrItem, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setSelectedQrIndex(idx)}
                          className={`w-full text-left p-3 rounded-lg border text-xs transition flex items-start gap-3 cursor-pointer ${
                            selectedQrIndex === idx
                              ? 'bg-white border-amber-500 shadow-sm ring-2 ring-amber-400/40'
                              : 'bg-white/70 hover:bg-white border-amber-200/80 text-slate-700'
                          }`}
                        >
                          <div className={`w-4 h-4 rounded-full mt-0.5 border flex items-center justify-center shrink-0 ${
                            selectedQrIndex === idx ? 'border-amber-600 bg-amber-600' : 'border-slate-300 bg-white'
                          }`}>
                            {selectedQrIndex === idx && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-slate-900 leading-snug">
                              "{qrItem.nearby_text}"
                            </div>
                            <div className="text-[11px] text-slate-500 flex flex-wrap gap-x-3 mt-1 font-mono">
                              {qrItem.location_description && <span>Location: {qrItem.location_description}</span>}
                              {qrItem.target_url && <span className="text-indigo-600 font-medium">{qrItem.target_url}</span>}
                              {qrItem.code_to_enter && <span>Code: {qrItem.code_to_enter}</span>}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {(() => {
                  const activeComplianceQr = (jobStatus.available_compliance_qrs && jobStatus.available_compliance_qrs[selectedQrIndex]) || null;
                  const defaultUrl = activeComplianceQr?.target_url || jobStatus.detected_qr_url;
                  const effectiveUrl = customPortalUrl || defaultUrl;
                  const activeCode = activeComplianceQr?.code_to_enter || jobStatus.code_to_enter;
                  return (
                    <>
                      {/* Step 1: Open Portal */}
                      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-black">1</span>
                            <span>{t('scan.qr_step1_title')}</span>
                          </span>
                          <button
                            type="button"
                            onClick={() => setIsEditingUrl(!isEditingUrl)}
                            className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold underline cursor-pointer"
                          >
                            {isEditingUrl ? t('common.save') : t('common.edit')}
                          </button>
                        </div>
                        {isEditingUrl ? (
                          <div className="pt-1 flex gap-2">
                            <input
                              type="url"
                              value={effectiveUrl || ''}
                              onChange={(e) => setCustomPortalUrl(e.target.value)}
                              placeholder="https://bingosnacks.com/factory-locator.html?m=k"
                              className="flex-1 px-3 py-1.5 text-xs font-mono bg-white border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                            />
                            {effectiveUrl && (
                              <a
                                href={effectiveUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition shrink-0"
                              >
                                <span>{t('common.open')}</span>
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                          </div>
                        ) : (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                            <div className="text-xs text-slate-600 break-all font-mono">
                              {effectiveUrl || t('common.na')}
                            </div>
                            {effectiveUrl && (
                              <a
                                href={effectiveUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition shrink-0"
                              >
                                <span>{t('common.open_portal')}</span>
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Step 2: Batch Code Verification & Slicing */}
                      <div className="bg-indigo-50/70 p-4 rounded-xl border border-indigo-100 space-y-4">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-indigo-100/80 pb-3">
                          <span className="text-xs font-bold uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
                            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-black">2</span>
                            <span>{t('scan.qr_step2_title')}</span>
                          </span>
                          {/* Batch Code Presence Selector */}
                          <div className="inline-flex rounded-lg bg-white p-0.5 border border-indigo-200 text-xs">
                            <button
                              type="button"
                              onClick={() => setBatchCodePresence('present')}
                              className={`px-3 py-1 rounded-md font-semibold transition cursor-pointer ${
                                batchCodePresence === 'present'
                                  ? 'bg-indigo-600 text-white shadow-xs'
                                  : 'text-slate-600 hover:text-slate-900'
                              }`}
                            >
                              {t('scan.qr_batch_present_option')}
                            </button>
                            <button
                              type="button"
                              onClick={() => setBatchCodePresence('absent')}
                              className={`px-3 py-1 rounded-md font-semibold transition cursor-pointer ${
                                batchCodePresence === 'absent'
                                  ? 'bg-amber-600 text-white shadow-xs'
                                  : 'text-slate-600 hover:text-slate-900'
                              }`}
                            >
                              {t('scan.qr_batch_absent_option')}
                            </button>
                          </div>
                        </div>

                        {batchCodePresence === 'absent' ? (
                          <div className="space-y-3 bg-amber-50/80 p-3.5 rounded-lg border border-amber-200">
                            <div className="flex items-start gap-2.5">
                              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                              <div className="text-xs text-amber-900 space-y-1">
                                <p className="font-bold">{t('scan.qr_no_batch_title')}</p>
                                <p className="leading-relaxed text-amber-800">
                                  {t('scan.qr_no_batch_desc')}
                                </p>
                              </div>
                            </div>
                            <div className="flex justify-end pt-1">
                              <button
                                type="button"
                                disabled={isSubmittingNoBatchCode}
                                onClick={handleConfirmNoBatchCode}
                                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center gap-2 cursor-pointer"
                              >
                                <span>{isSubmittingNoBatchCode ? t('scan.qr_no_batch_btn_loading') : t('scan.qr_no_batch_btn')}</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="text-xs text-indigo-900 leading-relaxed">
                              <span className="font-semibold text-indigo-950">{t('scan.qr_batch_reference_label')}</span>{' '}
                              {t('scan.qr_batch_reference_hint')}
                            </div>

                            {/* Low Confidence Warning Banner */}
                            {(jobStatus.batch_code_confidence === 'low' || jobStatus.batch_code_flag) && (
                              <div className="bg-amber-50 border border-amber-200 text-amber-900 p-2.5 rounded-lg text-xs flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                                <span className="font-medium leading-relaxed">
                                  {jobStatus.batch_code_flag || t('scan.qr_batch_low_confidence')}
                                </span>
                              </div>
                            )}

                            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                              <div className="relative flex-1">
                                <input
                                  type="text"
                                  value={editableBatchCode !== '' ? editableBatchCode : (activeCode || '')}
                                  onChange={(e) => setEditableBatchCode(e.target.value)}
                                  placeholder={t('scan.qr_batch_input_placeholder')}
                                  className="w-full font-mono text-base font-bold text-indigo-950 bg-white px-4 py-2.5 rounded-lg border-2 border-indigo-300 focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 tracking-wider shadow-sm uppercase placeholder:normal-case placeholder:font-normal placeholder:text-slate-400 placeholder:text-xs"
                                />
                              </div>
                              <button
                                type="button"
                                onClick={() => {
                                  const codeToCopy = editableBatchCode !== '' ? editableBatchCode : (activeCode || '');
                                  if (codeToCopy) {
                                    navigator.clipboard.writeText(codeToCopy);
                                    setCopiedCode(true);
                                    setTimeout(() => setCopiedCode(false), 2000);
                                  }
                                }}
                                className="px-4 py-2.5 bg-white hover:bg-slate-100 border border-indigo-200 rounded-lg text-indigo-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition shrink-0 shadow-xs cursor-pointer"
                                title="Copy code to clipboard"
                              >
                                {copiedCode ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                                <span>{copiedCode ? t('common.copied') : t('common.copy')}</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  );
                })()}

                {/* Step 3: Screenshot Upload (Visible only when batch code is present) */}
                {batchCodePresence === 'present' && (
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                        <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-black">3</span>
                        <span>{t('scan.qr_step3_title')}</span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">
                      {t('scan.qr_screenshot_hint')}
                    </p>

                    <div className="flex flex-col sm:flex-row items-center gap-3 pt-1">
                      <input
                        ref={qrFileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            setQrScreenshot(e.target.files[0]);
                          }
                        }}
                        className="hidden"
                      />
                      <button
                        type="button"
                        onClick={() => qrFileInputRef.current?.click()}
                        className="w-full sm:w-auto px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-2 truncate cursor-pointer"
                      >
                        <Upload className="w-4 h-4 text-slate-500" />
                        <span className="truncate">{qrScreenshot ? qrScreenshot.name : t('scan.qr_choose_screenshot')}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => mobileQrCameraInputRef.current?.click()}
                        className="w-full sm:w-auto px-3.5 py-2.5 bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1.5 cursor-pointer"
                        title="Snap photo with camera"
                      >
                        <Camera className="w-4 h-4 text-slate-600" />
                        <span>Take Photo</span>
                      </button>
                      <button
                        type="button"
                        disabled={!qrScreenshot || isUploadingQr}
                        onClick={handleUploadQrEvidence}
                        className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
                      >
                        <span>{isUploadingQr ? t('scan.qr_btn_submitting') : t('scan.qr_btn_submit_screenshot')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Step 4: Skip Verification Option */}
              <div className="border-t border-slate-100 pt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <p className="text-slate-500 text-[11px] leading-relaxed">
                  {t('scan.qr_step4_desc')}
                </p>
                <button
                  type="button"
                  disabled={isSkippingQr}
                  onClick={handleSkipQrVerification}
                  className="px-3.5 py-1.5 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-300 rounded-lg transition font-semibold shrink-0 cursor-pointer"
                >
                  {isSkippingQr ? t('common.loading') : t('scan.qr_step4_title')}
                </button>
              </div>
            </div>
          ) : (
            <StageProgressBar
              status={jobStatus.status}
              progressPercentage={jobStatus.progress_percentage}
              stageMessage={jobStatus.current_stage_message}
            />
          )}
        </div>
      )}

      {/* VIEW 3: ANNOTATED RESULTS & RULE CHECKLIST */}
      {scanResult && !isScanning && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Canvas: Annotated Label Image View */}
          <div className="lg:col-span-7 h-[640px]">
            <AnnotatedImageViewer
              imageUrl={scanResult.image_url}
              imageUrls={scanResult.image_urls && scanResult.image_urls.length > 0 ? scanResult.image_urls : [scanResult.image_url]}
              activePanelIndex={activePanelIndex}
              onPanelChange={setActivePanelIndex}
              ruleResults={scanResult.rule_results}
              rawTokens={scanResult.raw_ocr_tokens}
              extractedData={scanResult.extracted_data}
              selectedRuleId={selectedRuleId}
              onSelectRule={handleSelectRule}
            />
          </div>

          {/* Right Panel: Rule-by-rule Checklist */}
          <div className="lg:col-span-5 h-[640px]">
            <RuleChecklistPanel
              scanId={scanResult.id}
              productName={scanResult.product_name}
              category={scanResult.category}
              inspectorName={scanResult.inspector_name}
              createdAt={scanResult.created_at}
              ruleResults={scanResult.rule_results}
              overallVerdict={scanResult.overall_compliance_verdict}
              complianceScore={scanResult.compliance_score}
              selectedRuleId={selectedRuleId}
              onSelectRule={handleSelectRule}
              onViewReport={() => onViewReport(scanResult.id)}
            />
          </div>

        </div>

        {/* Supplementary Statutory Audits & QR Attended Verification */}
        {(() => {
          const master = scanResult.extracted_data?.master_report;
          const mfg = master?.manufacturer_details || scanResult.extracted_data?.manufacturer_details;
          const usp = master?.usp_cross_verification || scanResult.extracted_data?.usp_cross_verification;
          const shrink = master?.second_schedule_shrinkflation_audit || scanResult.extracted_data?.second_schedule_shrinkflation_audit;
          const detectedQrUrl = scanResult.detected_qr_url || master?.qr_code_detected_url;
          const codeToEnter = scanResult.code_to_enter || mfg?.batch_code_used;
          const isQrPending = Boolean(
            detectedQrUrl ||
            mfg?.resolution_method === 'QR_PORTAL_ATTENDED_REQUIRED' ||
            mfg?.resolution_method === 'UNRESOLVED' ||
            (mfg?.compliance_remarks && mfg.compliance_remarks.toLowerCase().includes('qr'))
          ) && (!mfg?.is_compliant || !mfg?.resolved_address || !mfg?.resolved_address.match(/\d{6}/))
          && mfg?.resolution_method !== 'NO_BATCH_CODE_ON_PACKAGE';

          return (
            <div className="space-y-4">
              {/* QR Attended Verification Banner (Pending State) */}
              {isQrPending && (
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-xl p-5 shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-10 h-10 bg-indigo-600 text-white rounded-lg flex items-center justify-center shrink-0 shadow-sm">
                        <QrCode className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-bold text-indigo-950">{t('scan.qr_card_title')}</h4>
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                            {t('scan.qr_card_pending')}
                          </span>
                        </div>
                        <p className="text-xs text-indigo-800 mt-1 leading-relaxed">
                          {t('scan.qr_card_desc')}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    {/* Link to Manufacturer Portal */}
                    <div className="bg-white p-3.5 rounded-lg border border-indigo-100 flex items-center justify-between gap-3 shadow-xs">
                      <div className="min-w-0">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">{t('scan.qr_portal_url_label')}</span>
                        <span className="text-xs font-mono font-medium text-slate-700 truncate block" title={detectedQrUrl || undefined}>
                          {detectedQrUrl || 'Portal link available'}
                        </span>
                      </div>
                      {detectedQrUrl && (
                        <a
                          href={detectedQrUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow-sm transition shrink-0 cursor-pointer"
                        >
                          <span>{t('common.open_portal')}</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      )}
                    </div>

                    {/* Batch Code to Enter */}
                    <div className="bg-white p-3.5 rounded-lg border border-indigo-100 flex items-center justify-between gap-3 shadow-xs">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">{t('scan.qr_batch_code_label')}</span>
                        <span className="text-sm font-mono font-black text-indigo-950 tracking-wider">
                          {codeToEnter || 'Check Batch on Pack'}
                        </span>
                      </div>
                      {codeToEnter && (
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(codeToEnter);
                            setCopiedCode(true);
                            setTimeout(() => setCopiedCode(false), 2000);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-semibold transition cursor-pointer"
                          title="Copy batch code"
                        >
                          {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedCode ? t('common.copied') : t('common.copy')}</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Screenshot Upload & Re-verify Action */}
                  <div className="bg-white/80 p-3.5 rounded-lg border border-indigo-100 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <div className="text-xs text-slate-600">
                      {t('scan.qr_screenshot_hint')}
                    </div>
                    <div className="flex items-center space-x-2 w-full sm:w-auto shrink-0">
                      <input
                        ref={qrFileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            setQrScreenshot(e.target.files[0]);
                          }
                        }}
                        className="hidden"
                      />
                      <button
                        type="button"
                        onClick={() => qrFileInputRef.current?.click()}
                        className="flex-1 sm:flex-initial px-3 py-1.5 bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-lg transition truncate max-w-[200px] cursor-pointer"
                      >
                        {qrScreenshot ? qrScreenshot.name : t('scan.qr_choose_screenshot')}
                      </button>
                      <button
                        type="button"
                        disabled={!qrScreenshot || isUploadingQr}
                        onClick={handleUploadQrEvidence}
                        className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition flex items-center space-x-1.5 shadow-sm shrink-0 cursor-pointer"
                      >
                        <Upload className="w-3.5 h-3.5" />
                        <span>{isUploadingQr ? t('scan.qr_btn_submitting') : t('scan.qr_btn_submit_screenshot')}</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* QR Attended Verification (Verified State) */}
              {!isQrPending && mfg?.resolution_method === 'QR_PORTAL_ATTENDED' && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 bg-emerald-600 text-white rounded-lg flex items-center justify-center shrink-0 shadow-xs">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wide">
                        {t('scan.qr_verified_title')}
                      </h4>
                      <p className="text-xs text-emerald-800 font-medium mt-0.5">
                        {mfg.resolved_manufacturer_name} — {mfg.resolved_address}
                      </p>
                    </div>
                  </div>
                  {detectedQrUrl && (
                    <a
                      href={detectedQrUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-emerald-300 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-lg transition shrink-0 cursor-pointer"
                    >
                      <span>{t('common.open_portal')}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              )}

              {/* No Batch Code on Package (Distinct Manual Inspection State) */}
              {!isQrPending && mfg?.resolution_method === 'NO_BATCH_CODE_ON_PACKAGE' && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 bg-amber-600 text-white rounded-lg flex items-center justify-center shrink-0 shadow-xs">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-amber-950 uppercase tracking-wide">
                        {t('scan.qr_no_batch_result_title')}
                      </h4>
                      <p className="text-xs text-amber-800 font-medium mt-0.5">
                        {mfg.compliance_remarks || 'Manufacturer portal verification required, but no batch code was found on the package to enter. Flagged for physical manual inspection.'}
                      </p>
                    </div>
                  </div>
                  {detectedQrUrl && (
                    <a
                      href={detectedQrUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-amber-300 hover:bg-amber-100 text-amber-800 text-xs font-semibold rounded-lg transition shrink-0 cursor-pointer"
                    >
                      <span>{t('common.open_portal')}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              )}

              {/* Statutory Metrology Audits Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* USP Mathematical Verification Card */}
                {usp && (
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between border-b pb-2">
                      <div className="flex items-center space-x-2">
                        <Calculator className="w-4 h-4 text-blue-600" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                          {t('scan.usp_audit_title')}
                        </h4>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        usp.is_compliant ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                      }`}>
                        {usp.is_compliant ? t('scan.usp_accurate') : 'USP Discrepancy'}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center py-1">
                      <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                        <div className="text-[10px] text-slate-500 font-semibold">Declared MRP</div>
                        <div className="text-xs font-bold text-slate-800">₹ {usp.mrp_numeric ?? 'N/A'}</div>
                      </div>
                      <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                        <div className="text-[10px] text-slate-500 font-semibold">Declared USP</div>
                        <div className="text-xs font-bold text-slate-800">{usp.declared_usp_raw || (usp.declared_usp_numeric ? `₹ ${usp.declared_usp_numeric}` : 'N/A')}</div>
                      </div>
                      <div className="bg-blue-50 p-2 rounded-lg border border-blue-100">
                        <div className="text-[10px] text-blue-600 font-semibold">Calculated Base</div>
                        <div className="text-xs font-bold text-blue-900">₹ {usp.calculated_usp_per_base_unit} {usp.calculated_usp_unit}</div>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 leading-snug">{usp.remarks}</p>
                  </div>
                )}

                {/* Second Schedule Anti-Shrinkflation Audit Card */}
                {shrink && (
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between border-b pb-2">
                      <div className="flex items-center space-x-2">
                        <Scale className="w-4 h-4 text-blue-600" />
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                          Second Schedule Anti-Shrinkflation Audit
                        </h4>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        shrink.is_compliant ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                      }`}>
                        {shrink.is_compliant ? 'Standard Pack Size' : 'Non-Standard Size'}
                      </span>
                    </div>
                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between text-slate-700">
                        <span className="text-slate-500">Commodity Category:</span>
                        <span className="font-semibold">{shrink.matched_commodity_category || 'Not restricted under Schedule II'}</span>
                      </div>
                      <div className="flex justify-between text-slate-700">
                        <span className="text-slate-500">Declared Quantity:</span>
                        <span className="font-mono font-bold">{shrink.declared_quantity || 'N/A'}</span>
                      </div>
                      {shrink.prescribed_pack_sizes_sample && shrink.prescribed_pack_sizes_sample.length > 0 && (
                        <div className="flex justify-between text-slate-700">
                          <span className="text-slate-500">Permitted Pack Sizes:</span>
                          <span className="font-mono text-[11px] text-blue-700">{shrink.prescribed_pack_sizes_sample.join(', ')}</span>
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 leading-snug">{shrink.remarks}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
        </div>
      )}

    </div>
  );
};
