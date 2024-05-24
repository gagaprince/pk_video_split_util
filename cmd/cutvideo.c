#include <libavformat/avformat.h>
#include <libavutil/timestamp.h>
#include <libavutil/avutil.h>
#include <libavcodec/avcodec.h>
#include <stdio.h>
// #include <stdlib.h>

// /usr/bin/clang /Users/wangzidong/my_work/ffmpeg_ctest/cutvideo.c -o /Users/wangzidong/my_work/ffmpeg_ctest/cutvideo -I /opt/homebrew/Cellar/ffmpeg/6.1.1_5/include -L /opt/homebrew/Cellar/ffmpeg/6.1.1_5/lib -lavutil -lavcodec -lavformat

static void log_packet(const AVFormatContext *fmt_ctx, const AVPacket *pkt, const char *tag)
{
    AVRational *time_base = &fmt_ctx->streams[pkt->stream_index]->time_base;

    printf("%s: pts:%s pts_time:%s dts:%s dts_time:%s duration:%s duration_time:%s stream_index:%d\n",
           tag,
           av_ts2str(pkt->pts), av_ts2timestr(pkt->pts, time_base),
           av_ts2str(pkt->dts), av_ts2timestr(pkt->dts, time_base),
           av_ts2str(pkt->duration), av_ts2timestr(pkt->duration, time_base),
           pkt->stream_index);
}

int cut_video(double from_seconds, double end_seconds, const char* in_filename, const char* out_filename) {
    AVFormatContext *ifmt_ctx = NULL, *ofmt_ctx = NULL;
    AVOutputFormat *ofmt = NULL;
    AVPacket pkt;
    int ret, i;

    avformat_open_input(&ifmt_ctx, in_filename, 0, 0);
    if (!ifmt_ctx) {
        fprintf(stderr, "Could not open input file '%s'\n", in_filename);
        return -1;
    }

    if (avformat_find_stream_info(ifmt_ctx, 0) < 0) {
        fprintf(stderr, "Failed to retrieve input stream information\n");
        return -1;
    }

    av_dump_format(ifmt_ctx, 0, in_filename, 0);

    avformat_alloc_output_context2(&ofmt_ctx, NULL, NULL, out_filename);
    if (!ofmt_ctx) {
        fprintf(stderr, "Could not create output context\n");
        return -1;
    }

    ofmt = ofmt_ctx->oformat;

    for (i = 0; i < ifmt_ctx->nb_streams; i++) {
        AVStream *in_stream = ifmt_ctx->streams[i];
        AVStream *out_stream = avformat_new_stream(ofmt_ctx, NULL);
        out_stream->time_base = in_stream->time_base;
        if (!out_stream) {
            fprintf(stderr, "Failed allocating output stream\n");
            return -1;
        }

        if (avcodec_parameters_copy(out_stream->codecpar, in_stream->codecpar) < 0) {
            fprintf(stderr, "Failed to copy codec parameters\n");
            return -1;
        }
    }

    av_dump_format(ofmt_ctx, 0, out_filename, 1);

    if (!(ofmt->flags & AVFMT_NOFILE)) {
        if (avio_open(&ofmt_ctx->pb, out_filename, AVIO_FLAG_WRITE) < 0) {
            fprintf(stderr, "Could not open output file '%s'\n", out_filename);
            return -1;
        }
    }

    if (avformat_write_header(ofmt_ctx, NULL) < 0) {
        fprintf(stderr, "Error occurred when opening output file\n");
        return -1;
    }

    ret = av_seek_frame(ifmt_ctx, -1, from_seconds * AV_TIME_BASE, AVSEEK_FLAG_BACKWARD);
    if (ret < 0) {
        fprintf(stderr, "Error seek\n");
        return -1;
    }

    // while (1) {
    //     AVStream *in_stream, *out_stream;

    //     ret = av_read_frame(ifmt_ctx, &pkt);
    //     if (ret < 0) break;

    //     in_stream  = ifmt_ctx->streams[pkt.stream_index];
    //     out_stream = ofmt_ctx->streams[pkt.stream_index];

    //     printf("jump?");
    //     // 跳过非关键帧，直到找到第一个关键帧
    //     if (pkt.flags & AV_PKT_FLAG_KEY) {
    //         break;
    //     }
    //     printf("jump!");
    //     av_packet_unref(&pkt);
    // }

    int64_t *dts_start_from = malloc(sizeof(int64_t) * ifmt_ctx->nb_streams);
    memset(dts_start_from, 0, sizeof(int64_t) * ifmt_ctx->nb_streams);
    int64_t *pts_start_from = malloc(sizeof(int64_t) * ifmt_ctx->nb_streams);
    memset(pts_start_from, 0, sizeof(int64_t) * ifmt_ctx->nb_streams);

    while (1) {
        AVStream *in_stream, *out_stream;

        ret = av_read_frame(ifmt_ctx, &pkt);
        if (ret < 0) break;

        in_stream  = ifmt_ctx->streams[pkt.stream_index];
        out_stream = ofmt_ctx->streams[pkt.stream_index];

        if (av_q2d(in_stream->time_base) * pkt.pts > end_seconds) {
            av_packet_unref(&pkt);
            break;
        }


        if (dts_start_from[pkt.stream_index] == 0) {
//            if(pkt.dts!=pkt.pts){
//                printf("dts!=pts jump");
//                continue;
//            }
            dts_start_from[pkt.stream_index] = pkt.dts;
//            printf("stream_index: %d, dts_start_from: %s\n", pkt.stream_index ,av_ts2str(dts_start_from[pkt.stream_index]));
        }
        if (pts_start_from[pkt.stream_index] == 0) {
//            if(pkt.pts<=0){
//                continue;
//            }
            if(pkt.pts>pkt.dts){
                pkt.pts = pkt.dts;
            }
            pts_start_from[pkt.stream_index] = pkt.pts;
//            printf("stream_index: %d, pts_start_from: %s\n", pkt.stream_index ,av_ts2str(pts_start_from[pkt.stream_index]));
        }

        // log_packet(ifmt_ctx, &pkt, "in");
        // out_stream->time_base = in_stream->time_base;
//        printf("old pkt.pts %d: %ld \n", pkt.stream_index, pkt.pts);
//        printf("old pkt.dts %d: %ld \n", pkt.stream_index, pkt.dts);
        pkt.pts = av_rescale_q_rnd(pkt.pts - pts_start_from[pkt.stream_index], in_stream->time_base, out_stream->time_base, AV_ROUND_NEAR_INF|AV_ROUND_PASS_MINMAX);
        pkt.dts = av_rescale_q_rnd(pkt.dts - dts_start_from[pkt.stream_index], in_stream->time_base, out_stream->time_base, AV_ROUND_NEAR_INF|AV_ROUND_PASS_MINMAX);
//        printf("new pkt.pts %d: %ld \n", pkt.stream_index, pkt.pts);
//        printf("new pkt.dts %d: %ld \n", pkt.stream_index, pkt.dts);
        if (pkt.pts < 0) {
            pkt.pts = 0;
        }
        if (pkt.dts < 0) {
            pkt.dts = 0;
        }
        pkt.duration = (int)av_rescale_q((int64_t)pkt.duration, in_stream->time_base, out_stream->time_base);
        // pkt.pts = av_rescale_q_rnd(pkt.pts, in_stream->time_base, out_stream->time_base, AV_ROUND_NEAR_INF|AV_ROUND_PASS_MINMAX);
        // pkt.dts = av_rescale_q_rnd(pkt.dts, in_stream->time_base, out_stream->time_base, AV_ROUND_NEAR_INF|AV_ROUND_PASS_MINMAX);
        // pkt.duration = av_rescale_q(pkt.duration, in_stream->time_base, out_stream->time_base);
        pkt.pos = -1;

        // log_packet(ofmt_ctx, &pkt, "out");

        if (av_interleaved_write_frame(ofmt_ctx, &pkt) < 0) {
            printf("dts_start_from[pkt.stream_index] : %ld \n", dts_start_from[pkt.stream_index]);
            printf("pts_start_from[pkt.stream_index] : %ld \n", pts_start_from[pkt.stream_index]);
            fprintf(stderr, "Error muxing packet\n");
//            break;
        }
        av_packet_unref(&pkt);
    }

    av_write_trailer(ofmt_ctx);

    avformat_close_input(&ifmt_ctx);

    if (!(ofmt->flags & AVFMT_NOFILE)) {
        avio_closep(&ofmt_ctx->pb);
    }

    avformat_free_context(ofmt_ctx);

    return 0;
}

int main(int argc, char *argv[]){
    if(argc < 5){
        double startime = 13;
        double endtime = 26;
        char* src = "/Users/wangzidong/Downloads/baidu/枫糖/2024-05-15--06-36-44/out/0_2340.mp4";
        char* videoDst = "/Users/wangzidong/Downloads/baidu/枫糖/2024-05-15--06-36-44/out/output_split_video.mp4";
        cut_video(startime, endtime, src, videoDst);
    }
    double startime = atoi(argv[1]);
    double endtime = atoi(argv[2]);
    cut_video(startime, endtime, argv[3], argv[4]);
    return 0;
}

